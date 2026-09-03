'use client'

import axios from "../../../../plugins/axios"
import { getApiErrorMessage} from "../../../../plugins/apiError"
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

type Rating = 'G' | 'PG12' | 'R15' | 'R18'

type Movie = {
    id: number
    title: string
    description: string
    duration_minutes: number
    release_date: string
    rating: Rating
}

type MovieFormState = {
    title: string
    description: string
    duration_minutes: string
    release_date: string
    rating: Rating
}

const emptyForm: MovieFormState = {
    title: '',
    description: '',
    duration_minutes: '',
    release_date: '',
    rating: 'G',
}

const ratingOptions: Array<{ value: Rating; label: string }> = [
    { value: 'G', label: 'G(全年齢)' },
    { value: 'PG12', label: 'PG12' },
    { value: 'R15', label: 'R15' },
    { value: 'R18', label: 'R18' },
]

export default function AdminMoviesPage() {
    const [movies, setMovies] = useState<Array<Movie>>([])
    const [dialogOpen, setDialogOpen] = useState(false)
    const [editingId, setEditingId] = useState<number | null>(null)
    const [form, setForm] = useState<MovieFormState>(emptyForm)
    const [errorMessage, setErrorMessage] = useState('')
    const [successMessage, setSuccessMessage] = useState('')
    const [deleteTarget, setDeleteTarget] = useState<Movie | null>(null)

    const fetchMovies = () => {
        axios
            .get('/api/cinema/admin/movies/')
            .then((res) => setMovies(res.data))
            .catch(() => setErrorMessage('映画一覧の取得に失敗しました。'))
    }

    useEffect(() => {
        fetchMovies()
    }, [])

    const openCreateDialog = () => {
        setEditingId(null)
        setForm(emptyForm)
        setDialogOpen(true)
    }

    const openEditDialog = (movie: Movie) => {
        setEditingId(movie.id)
        setForm({
            title: movie.title,
            description: movie.description,
            duration_minutes: String(movie.duration_minutes),
            release_date: movie.release_date,
            rating: movie.rating,
        })
        setDialogOpen(true)
    }

    const closeDialog = () => {
        setDialogOpen(false)
    }

    const handleChange = (field: keyof MovieFormState, value: string) => {
        setForm((prev) => ({ ...prev, [field]: value }))
    }

    const handleSubmit = () => {
        const payload = {
            title: form.title,
            description: form.description,
            duration_minutes: Number(form.duration_minutes),
            release_date: form.release_date,
            rating: form.rating,
        }

        const request = editingId
            ? axios.put(`/api/cinema/admin/movies/${editingId}/`, payload)
            : axios.post('/api/cinema/admin/movies/', payload)

        request
            .then(() => {
                setSuccessMessage(editingId ? '映画情報を更新しました。' : '映画を登録しました。')
                setDialogOpen(false)
                fetchMovies()
            })
            .catch((err) => {
                const detail = getApiErrorMessage(err, '保存に失敗しました。入力内容を確認してください。')
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
            .delete(`/api/cinema/admin/movies/${deleteTarget.id}/`)
            .then(() => {
                setSuccessMessage('映画を削除しました。')
                setDeleteTarget(null)
                fetchMovies()
            })
            .catch(() => {
                setErrorMessage('削除に失敗しました。既に上映回が登録されている可能性があります。')
                setDeleteTarget(null)
            })
    }

    return (
        <Box>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 3 }}>
                <Typography variant="h5">映画管理</Typography>
                <Button variant="contained" startIcon={<AddIcon />} onClick={openCreateDialog}>
                    新規登録
                </Button>
            </Box>

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>タイトル</TableCell>
                            <TableCell>上映時間</TableCell>
                            <TableCell>公開日</TableCell>
                            <TableCell>レーティング</TableCell>
                            <TableCell align="right">操作</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {movies.map((movie) => (
                            <TableRow key={movie.id}>
                                <TableCell>{movie.title}</TableCell>
                                <TableCell>{movie.duration_minutes}分</TableCell>
                                <TableCell>{movie.release_date}</TableCell>
                                <TableCell>{movie.rating}</TableCell>
                                <TableCell align="right">
                                    <IconButton onClick={() => openEditDialog(movie)}>
                                        <EditIcon fontSize="small" />
                                    </IconButton>
                                    <IconButton onClick={() => setDeleteTarget(movie)}>
                                        <DeleteIcon fontSize="small" />
                                    </IconButton>
                                </TableCell>
                            </TableRow>
                        ))}
                        {movies.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={5} align="center">
                                    登録されている映画がありません。
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* 新規作成・編集ダイアログ */}
            <Dialog open={dialogOpen} onClose={closeDialog} fullWidth maxWidth="desktop">
                <DialogTitle>{editingId ? '映画情報の編集' : '映画の新規登録'}</DialogTitle>
                <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2, marginTop: 1 }}>
                    <TextField
                        label="タイトル"
                        value={form.title}
                        onChange={(e) => handleChange('title', e.target.value)}
                        required
                        fullWidth
                    />
                    <TextField
                        label="あらすじ"
                        value={form.description}
                        onChange={(e) => handleChange('description', e.target.value)}
                        multiline
                        minRows={3}
                        fullWidth
                    />
                    <TextField
                        label="上映時間(分)"
                        type="number"
                        value={form.duration_minutes}
                        onChange={(e) => handleChange('duration_minutes', e.target.value)}
                        required
                        fullWidth
                    />
                    <TextField
                        label="公開日"
                        type="date"
                        value={form.release_date}
                        onChange={(e) => handleChange('release_date', e.target.value)}
                        slotProps={{ inputLabel: { shrink: true } }}
                        required
                        fullWidth
                    />
                    <TextField
                        select
                        label="レーティング"
                        value={form.rating}
                        onChange={(e) => handleChange('rating', e.target.value)}
                        fullWidth
                    >
                        {ratingOptions.map((option) => (
                            <MenuItem key={option.value} value={option.value}>
                                {option.label}
                            </MenuItem>
                        ))}
                    </TextField>
                </DialogContent>
                <DialogActions>
                    <Button onClick={closeDialog}>キャンセル</Button>
                    <Button variant="contained" onClick={handleSubmit}>
                        {editingId ? '更新する' : '登録する'}
                    </Button>
                </DialogActions>
            </Dialog>

            {/* 削除確認ダイアログ */}
            <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)}>
                <DialogTitle>映画の削除</DialogTitle>
                <DialogContent>
                    <Typography>
                        「{deleteTarget?.title}」を削除します。よろしいですか？
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