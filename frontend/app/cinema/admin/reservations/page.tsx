'use client'

import axios from "../../../../plugins/axios"
import {
    Alert,
    Box,
    Button,
    Chip,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    MenuItem,
    Paper,
    Snackbar,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TextField,
    Typography,
} from "@mui/material"
import { useEffect, useState } from "react"

type ReservationSeat = { id: number; seat_label: string }

type AdminReservation = {
    id: number
    username: string
    customer_name: string
    movie_title: string
    screen_name: string
    status: string
    status_display: string
    checked_in_at: string | null
    reserved_at: string
    total_price: number
    seats: Array<ReservationSeat>
    payment_status: string | null
    payment_status_display: string
}

const statusOptions = [
    { value: '', label: 'すべて' },
    { value: 'pending', label: '仮予約' },
    { value: 'confirmed', label: '確定' },
    { value: 'cancelled', label: 'キャンセル' },
]

export default function AdminReservationsPage() {
    const [reservations, setReservations] = useState<Array<AdminReservation>>([])
    const [statusFilter, setStatusFilter] = useState('')
    const [cancelTarget, setCancelTarget] = useState<AdminReservation | null>(null)
    const [errorMessage, setErrorMessage] = useState('')
    const [successMessage, setSuccessMessage] = useState('')

    const fetchReservations = () => {
        axios
            .get('/api/cinema/admin/reservations/', {
                params: statusFilter ? { status: statusFilter } : {},
            })
            .then((res) => setReservations(res.data))
            .catch(() => setErrorMessage('予約一覧の取得に失敗しました。'))
    }

    useEffect(() => {
        fetchReservations()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [statusFilter])

    const handleCancel = () => {
        if (!cancelTarget) return
        axios
            .post(`/api/cinema/admin/reservations/${cancelTarget.id}/cancel/`)
            .then(() => {
                setSuccessMessage('予約をキャンセルしました。')
                setCancelTarget(null)
                fetchReservations()
            })
            .catch((err) => {
                setErrorMessage(err.response?.data?.errMsg || 'キャンセルに失敗しました。')
                setCancelTarget(null)
            })
    }

    return (
        <Box>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 3 }}>
                <Typography variant="h5">予約管理</Typography>
                <TextField
                    select
                    label="ステータス"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    size="small"
                    sx={{ width: 160 }}
                >
                    {statusOptions.map((opt) => (
                        <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
                    ))}
                </TextField>
            </Box>

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>予約者</TableCell>
                            <TableCell>映画 / スクリーン</TableCell>
                            <TableCell>座席</TableCell>
                            <TableCell>ステータス</TableCell>
                            <TableCell>決済</TableCell>
                            <TableCell>金額</TableCell>
                            <TableCell align="right">操作</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {reservations.map((r) => (
                            <TableRow key={r.id}>
                                <TableCell>{r.customer_name}({r.username})</TableCell>
                                <TableCell>{r.movie_title} / {r.screen_name}</TableCell>
                                <TableCell>{r.seats.map((s) => s.seat_label).join(', ') || 'なし'}</TableCell>
                                <TableCell>
                                    <Chip
                                        label={r.status_display}
                                        size="small"
                                        color={r.status === 'cancelled' ? 'default' : r.status === 'confirmed' ? 'success' : 'warning'}
                                    />
                                </TableCell>
                                <TableCell>{r.payment_status_display || '-'}</TableCell>
                                <TableCell>{r.total_price.toLocaleString()}円</TableCell>
                                <TableCell align="right">
                                    {r.status !== 'cancelled' && (
                                        <Button
                                            size="small"
                                            color="error"
                                            onClick={() => setCancelTarget(r)}
                                        >
                                            キャンセル
                                        </Button>
                                    )}
                                </TableCell>
                            </TableRow>
                        ))}
                        {reservations.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={7} align="center">
                                    該当する予約がありません。
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </TableContainer>

            <Dialog open={!!cancelTarget} onClose={() => setCancelTarget(null)}>
                <DialogTitle>予約のキャンセル</DialogTitle>
                <DialogContent>
                    <Typography>
                        {cancelTarget?.customer_name}様の予約(ID: {cancelTarget?.id})を強制キャンセルします。よろしいですか？
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setCancelTarget(null)}>キャンセル</Button>
                    <Button color="error" variant="contained" onClick={handleCancel}>
                        実行する
                    </Button>
                </DialogActions>
            </Dialog>

            <Snackbar open={!!errorMessage} autoHideDuration={4000} onClose={() => setErrorMessage('')}>
                <Alert severity="error">{errorMessage}</Alert>
            </Snackbar>
            <Snackbar open={!!successMessage} autoHideDuration={3000} onClose={() => setSuccessMessage('')}>
                <Alert severity="success">{successMessage}</Alert>
            </Snackbar>
        </Box>
    )
}