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
import {
    Add as AddIcon,
    Delete as DeleteIcon,
    Edit as EditIcon,
} from "@mui/icons-material"
import { useEffect, useState } from "react"

type Theater = {
    id: number
    name: string
    address: string
}

type TheaterFormState = {
    name: string
    address: string
}

const emptyForm: TheaterFormState = {
    name: '',
    address: '',
}

export default function AdminTheatersPage() {
    const [theaters, setTheaters] = useState<Array<Theater>>([])
    const [dialogOpen, setDialogOpen] = useState(false)
    const [editingId, setEditingId] = useState<number | null>(null)
    const [form, setForm] = useState<TheaterFormState>(emptyForm)

    const [errorMessage, setErrorMessage] = useState('')
    const [successMessage, setSuccessMessage] = useState('')
    const [deleteTarget, setDeleteTarget] = useState<Theater | null>(null)

    const fetchTheaters = () => {
        axios
            .get('/api/cinema/theaters/')
            .then((res) => setTheaters(res.data))
            .catch(() => {
                setErrorMessage('劇場一覧の取得に失敗しました。')
            })
    }

    useEffect(() => {
        fetchTheaters()
    }, [])

    const openCreateDialog = () => {
        setEditingId(null)
        setForm(emptyForm)
        setDialogOpen(true)
    }

    const openEditDialog = (theater: Theater) => {
        setEditingId(theater.id)
        setForm({
            name: theater.name,
            address: theater.address,
        })
        setDialogOpen(true)
    }

    const closeDialog = () => {
        setDialogOpen(false)
    }

    const handleChange = (
        field: keyof TheaterFormState,
        value: string
    ) => {
        setForm((prev) => ({
            ...prev,
            [field]: value,
        }))
    }

    const handleSubmit = () => {
        const payload = {
            name: form.name,
            address: form.address,
        }

        const request = editingId
            ? axios.put(
                `/api/cinema/theaters/${editingId}/`,
                payload
            )
            : axios.post(
                '/api/cinema/theaters/',
                payload
            )

        request
            .then(() => {
                setSuccessMessage(
                    editingId
                        ? '劇場情報を更新しました。'
                        : '劇場を登録しました。'
                )
                setDialogOpen(false)
                fetchTheaters()
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
            .delete(
                `/api/cinema/theaters/${deleteTarget.id}/`
            )
            .then(() => {
                setSuccessMessage('劇場を削除しました。')
                setDeleteTarget(null)
                fetchTheaters()
            })
            .catch(() => {
                setErrorMessage(
                    '削除に失敗しました。スクリーンが登録されている可能性があります。'
                )
                setDeleteTarget(null)
            })
    }

    return (
        <Box>
            <Box
                sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 3,
                }}
            >
                <Typography variant="h5">
                    劇場管理
                </Typography>

                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={openCreateDialog}
                >
                    新規登録
                </Button>
            </Box>

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>劇場名</TableCell>
                            <TableCell>住所</TableCell>
                            <TableCell align="right">
                                操作
                            </TableCell>
                        </TableRow>
                    </TableHead>

                    <TableBody>
                        {theaters.map((theater) => (
                            <TableRow key={theater.id}>
                                <TableCell>
                                    {theater.name}
                                </TableCell>

                                <TableCell>
                                    {theater.address}
                                </TableCell>

                                <TableCell align="right">
                                    <IconButton
                                        onClick={() =>
                                            openEditDialog(theater)
                                        }
                                    >
                                        <EditIcon fontSize="small" />
                                    </IconButton>

                                    <IconButton
                                        onClick={() =>
                                            setDeleteTarget(theater)
                                        }
                                    >
                                        <DeleteIcon fontSize="small" />
                                    </IconButton>
                                </TableCell>
                            </TableRow>
                        ))}

                        {theaters.length === 0 && (
                            <TableRow>
                                <TableCell
                                    colSpan={3}
                                    align="center"
                                >
                                    登録されている劇場がありません。
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* 新規作成・編集 */}
            <Dialog
                open={dialogOpen}
                onClose={closeDialog}
                fullWidth
                maxWidth="desktop"
            >
                <DialogTitle>
                    {editingId
                        ? '劇場情報の編集'
                        : '劇場の新規登録'}
                </DialogTitle>

                <DialogContent
                    sx={{
                        display: "flex",
                        flexDirection: "column",
                        gap: 2,
                        marginTop: 1,
                    }}
                >
                    <TextField
                        label="劇場名"
                        value={form.name}
                        onChange={(e) =>
                            handleChange(
                                'name',
                                e.target.value
                            )
                        }
                        required
                        fullWidth
                    />

                    <TextField
                        label="住所"
                        value={form.address}
                        onChange={(e) =>
                            handleChange(
                                'address',
                                e.target.value
                            )
                        }
                        required
                        fullWidth
                    />
                </DialogContent>

                <DialogActions>
                    <Button onClick={closeDialog}>
                        キャンセル
                    </Button>

                    <Button
                        variant="contained"
                        onClick={handleSubmit}
                    >
                        {editingId
                            ? '更新する'
                            : '登録する'}
                    </Button>
                </DialogActions>
            </Dialog>

            {/* 削除確認 */}
            <Dialog
                open={!!deleteTarget}
                onClose={() => setDeleteTarget(null)}
            >
                <DialogTitle>
                    劇場の削除
                </DialogTitle>

                <DialogContent>
                    <Typography>
                        「{deleteTarget?.name}」を削除します。
                        よろしいですか？
                    </Typography>
                </DialogContent>

                <DialogActions>
                    <Button
                        onClick={() => setDeleteTarget(null)}
                    >
                        キャンセル
                    </Button>

                    <Button
                        color="error"
                        variant="contained"
                        onClick={handleDelete}
                    >
                        削除する
                    </Button>
                </DialogActions>
            </Dialog>

            <Snackbar
                open={!!errorMessage}
                autoHideDuration={4000}
                onClose={() => setErrorMessage('')}
            >
                <Alert severity="error">
                    {errorMessage}
                </Alert>
            </Snackbar>

            <Snackbar
                open={!!successMessage}
                autoHideDuration={3000}
                onClose={() => setSuccessMessage('')}
            >
                <Alert severity="success">
                    {successMessage}
                </Alert>
            </Snackbar>
        </Box>
    )
}