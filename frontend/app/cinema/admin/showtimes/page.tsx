'use client'

import axios from "../../../../plugins/axios"
import {
    Alert,
    Box,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    IconButton,
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
import { Add as AddIcon, Delete as DeleteIcon, Edit as EditIcon } from "@mui/icons-material"
import { useEffect, useState } from "react"

type Movie = { id: number; title: string; duration_minutes: number }
type Screen = { id: number; name: string; theater_name: string }

type Showtime = {
    id: number
    movie: number
    movie_title: string
    screen: number
    screen_name: string
    theater_name: string
    start_time: string
    end_time: string
    base_price: number
}

type ShowtimeFormState = {
    movie: string
    screen: string
    start_time: string
    end_time: string
    base_price: string
}

const emptyForm: ShowtimeFormState = {
    movie: '',
    screen: '',
    start_time: '',
    end_time: '',
    base_price: '',
}

// datetime-local用(秒・タイムゾーンを除いた形式)への変換
const toLocalInput = (iso: string) => iso ? iso.slice(0, 16) : ''

export default function AdminShowtimesPage() {
    const [showtimes, setShowtimes] = useState<Array<Showtime>>([])
    const [movies, setMovies] = useState<Array<Movie>>([])
    const [screens, setScreens] = useState<Array<Screen>>([])

    const [dialogOpen, setDialogOpen] = useState(false)
    const [editingId, setEditingId] = useState<number | null>(null)
    const [form, setForm] = useState<ShowtimeFormState>(emptyForm)

    const [errorMessage, setErrorMessage] = useState('')
    const [successMessage, setSuccessMessage] = useState('')
    const [deleteTarget, setDeleteTarget] = useState<Showtime | null>(null)

    const fetchShowtimes = () => {
        axios
            .get('/api/cinema/showtimes/')
            .then((res) => setShowtimes(res.data))
            .catch(() => setErrorMessage('上映回一覧の取得に失敗しました。'))
    }

    useEffect(() => {
        fetchShowtimes()
        axios.get('/api/cinema/movies/').then((res) => setMovies(res.data))
        axios.get('/api/cinema/screens/').then((res) => setScreens(res.data))
    }, [])

    const openCreateDialog = () => {
        setEditingId(null)
        setForm(emptyForm)
        setDialogOpen(true)
    }

    const openEditDialog = (showtime: Showtime) => {
        setEditingId(showtime.id)
        setForm({
            movie: String(showtime.movie),
            screen: String(showtime.screen),
            start_time: toLocalInput(showtime.start_time),
            end_time: toLocalInput(showtime.end_time),
            base_price: String(showtime.base_price),
        })
        setDialogOpen(true)
    }

    const closeDialog = () => setDialogOpen(false)

    const handleChange = (field: keyof ShowtimeFormState, value: string) => {
        if (field === 'start_time') {
            const movie = movies.find((m) => String(m.id) === form.movie)
            let autoEndTime = value

            if (movie && 'duration_minutes' in movie && value) {
                const TRAILER_MINUTES = 10
                const start = new Date(value)
                const totalMinutes = movie.duration_minutes + TRAILER_MINUTES
                const end = new Date(start.getTime() + totalMinutes * 60000)
                // datetime-local用にYYYY-MM-DDTHH:mm形式へ整形
                autoEndTime = end.toISOString().slice(0, 16)
            }

            setForm((prev) => ({
                ...prev,
                start_time: value,
                end_time: prev.end_time === '' ? autoEndTime : prev.end_time,
            }))
            return
        }
    setForm((prev) => ({ ...prev, [field]: value }))
    }

    const handleSubmit = () => {
        const payload = {
            movie: Number(form.movie),
            screen: Number(form.screen),
            start_time: form.start_time,
            end_time: form.end_time,
            base_price: Number(form.base_price),
        }

        const request = editingId
            ? axios.put(`/api/cinema/showtimes/${editingId}/`, payload)
            : axios.post('/api/cinema/showtimes/', payload)

        request
            .then(() => {
                setSuccessMessage(editingId ? '上映回を更新しました。' : '上映回を登録しました。')
                setDialogOpen(false)
                fetchShowtimes()
            })
            .catch((err) => {
                const detail = err.response?.data
                setErrorMessage(
                    detail && typeof detail === 'object'
                        ? Object.values(detail).flat().join(' / ')
                        : '保存に失敗しました。入力内容を確認してください。'
                )
            })
    }

    const handleDelete = () => {
        if (!deleteTarget) return
        axios
            .delete(`/api/cinema/showtimes/${deleteTarget.id}/`)
            .then(() => {
                setSuccessMessage('上映回を削除しました。')
                setDeleteTarget(null)
                fetchShowtimes()
            })
            .catch((err) => {
                setErrorMessage(
                    err.response?.data?.errMsg || '削除に失敗しました。既に予約が存在する可能性があります。'
                )
                setDeleteTarget(null)
            })
    }

    return (
        <Box>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 3 }}>
                <Typography variant="h5">上映回管理</Typography>
                <Button variant="contained" startIcon={<AddIcon />} onClick={openCreateDialog}>
                    新規登録
                </Button>
            </Box>

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>映画</TableCell>
                            <TableCell>劇場 / スクリーン</TableCell>
                            <TableCell>開始</TableCell>
                            <TableCell>終了</TableCell>
                            <TableCell>基本料金</TableCell>
                            <TableCell align="right">操作</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {showtimes.map((s) => (
                            <TableRow key={s.id}>
                                <TableCell>{s.movie_title}</TableCell>
                                <TableCell>{s.theater_name} / {s.screen_name}</TableCell>
                                <TableCell>{s.start_time.slice(0, 16).replace('T', ' ')}</TableCell>
                                <TableCell>{s.end_time.slice(0, 16).replace('T', ' ')}</TableCell>
                                <TableCell>{s.base_price.toLocaleString()}円</TableCell>
                                <TableCell align="right">
                                    <IconButton onClick={() => openEditDialog(s)}>
                                        <EditIcon fontSize="small" />
                                    </IconButton>
                                    <IconButton onClick={() => setDeleteTarget(s)}>
                                        <DeleteIcon fontSize="small" />
                                    </IconButton>
                                </TableCell>
                            </TableRow>
                        ))}
                        {showtimes.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={6} align="center">
                                    登録されている上映回がありません。
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </TableContainer>

            <Dialog open={dialogOpen} onClose={closeDialog} fullWidth maxWidth="desktop">
                <DialogTitle>{editingId ? '上映回の編集' : '上映回の新規登録'}</DialogTitle>
                <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2, marginTop: 1 }}>
                    <TextField
                        select
                        label="映画"
                        value={form.movie}
                        onChange={(e) => handleChange('movie', e.target.value)}
                        required
                        fullWidth
                    >
                        {movies.map((m) => (
                            <MenuItem key={m.id} value={m.id}>{m.title}</MenuItem>
                        ))}
                    </TextField>

                    <TextField
                        select
                        label="スクリーン"
                        value={form.screen}
                        onChange={(e) => handleChange('screen', e.target.value)}
                        required
                        fullWidth
                    >
                        {screens.map((s) => (
                            <MenuItem key={s.id} value={s.id}>{s.theater_name} / {s.name}</MenuItem>
                        ))}
                    </TextField>

                    <TextField
                        label="開始日時"
                        type="datetime-local"
                        value={form.start_time}
                        onChange={(e) => handleChange('start_time', e.target.value)}
                        slotProps={{ inputLabel: { shrink: true } }}
                        required
                        fullWidth
                    />

                    <TextField
                        label="終了日時"
                        type="datetime-local"
                        value={form.end_time}
                        onChange={(e) => handleChange('end_time', e.target.value)}
                        slotProps={{ inputLabel: { shrink: true } }}
                        required
                        fullWidth
                    />

                    <TextField
                        label="基本料金(円)"
                        type="number"
                        value={form.base_price}
                        onChange={(e) => handleChange('base_price', e.target.value)}
                        required
                        fullWidth
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={closeDialog}>キャンセル</Button>
                    <Button variant="contained" onClick={handleSubmit}>
                        {editingId ? '更新する' : '登録する'}
                    </Button>
                </DialogActions>
            </Dialog>

            <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)}>
                <DialogTitle>上映回の削除</DialogTitle>
                <DialogContent>
                    <Typography>
                        「{deleteTarget?.movie_title}」({deleteTarget?.start_time.slice(0, 16).replace('T', ' ')})を削除します。よろしいですか？
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteTarget(null)}>キャンセル</Button>
                    <Button color="error" variant="contained" onClick={handleDelete}>
                        削除する
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