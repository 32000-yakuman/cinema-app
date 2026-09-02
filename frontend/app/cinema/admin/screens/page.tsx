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
import {
    Add as AddIcon,
    Delete as DeleteIcon,
    Edit as EditIcon,
} from "@mui/icons-material"
import { useEffect, useState } from "react"

type Theater = {
    id: number
    name: string
}

type Screen = {
    id: number
    theater: number
    theater_name: string
    name: string
    row_count: number
    col_count: number
}

type ScreenFormState = {
    theater: string
    name: string
    row_count: string
    col_count: string
}

const emptyForm: ScreenFormState = {
    theater: '',
    name: '',
    row_count: '',
    col_count: '',
}

export default function AdminScreensPage() {
    const [screens, setScreens] = useState<Array<Screen>>([])
    const [theaters, setTheaters] = useState<Array<Theater>>([])

    const [dialogOpen, setDialogOpen] = useState(false)
    const [editingId, setEditingId] = useState<number | null>(null)

    const [form, setForm] =
        useState<ScreenFormState>(emptyForm)

    const [errorMessage, setErrorMessage] = useState('')
    const [successMessage, setSuccessMessage] = useState('')

    const [deleteTarget, setDeleteTarget] =
        useState<Screen | null>(null)

    const fetchScreens = () => {
        axios
            .get('/api/cinema/screens/')
            .then((res) => setScreens(res.data))
            .catch(() => {
                setErrorMessage(
                    'スクリーン一覧の取得に失敗しました。'
                )
            })
    }

    const fetchTheaters = () => {
        axios
            .get('/api/cinema/theaters/')
            .then((res) => setTheaters(res.data))
            .catch(() => {
                setErrorMessage(
                    '劇場一覧の取得に失敗しました。'
                )
            })
    }

    useEffect(() => {
        fetchScreens()
        fetchTheaters()
    }, [])

    const openCreateDialog = () => {
        setEditingId(null)
        setForm(emptyForm)
        setDialogOpen(true)
    }

    const openEditDialog = (screen: Screen) => {
        setEditingId(screen.id)

        setForm({
            theater: String(screen.theater),
            name: screen.name,
            row_count: String(screen.row_count),
            col_count: String(screen.col_count),
        })

        setDialogOpen(true)
    }

    const closeDialog = () => {
        setDialogOpen(false)
    }

    const handleChange = (
        field: keyof ScreenFormState,
        value: string
    ) => {
        setForm((prev) => ({
            ...prev,
            [field]: value,
        }))
    }

    const handleSubmit = () => {
        const payload = {
            theater: Number(form.theater),
            name: form.name,
            row_count: Number(form.row_count),
            col_count: Number(form.col_count),
        }

        const request = editingId
            ? axios.put(
                `/api/cinema/screens/${editingId}/`,
                payload
            )
            : axios.post(
                '/api/cinema/screens/',
                payload
            )

        request
            .then(() => {
                setSuccessMessage(
                    editingId
                        ? 'スクリーン情報を更新しました。'
                        : 'スクリーンを登録しました。'
                )

                setDialogOpen(false)
                fetchScreens()
            })
            .catch((err) => {
                const detail = err.response?.data

                setErrorMessage(
                    detail && typeof detail === 'object'
                        ? Object.values(detail)
                            .flat()
                            .join(' / ')
                        : '保存に失敗しました。入力内容を確認してください。'
                )
            })
    }

    const handleDelete = () => {
        if (!deleteTarget) return

        axios
            .delete(
                `/api/cinema/screens/${deleteTarget.id}/`
            )
            .then(() => {
                setSuccessMessage(
                    'スクリーンを削除しました。'
                )

                setDeleteTarget(null)
                fetchScreens()
            })
            .catch(() => {
                setErrorMessage(
                    '削除に失敗しました。座席や上映回が登録されている可能性があります。'
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
                    スクリーン管理
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
                            <TableCell>劇場</TableCell>
                            <TableCell>スクリーン名</TableCell>
                            <TableCell>座席行数</TableCell>
                            <TableCell>座席列数</TableCell>
                            <TableCell align="right">
                                操作
                            </TableCell>
                        </TableRow>
                    </TableHead>

                    <TableBody>
                        {screens.map((screen) => (
                            <TableRow key={screen.id}>
                                <TableCell>
                                    {screen.theater_name}
                                </TableCell>

                                <TableCell>
                                    {screen.name}
                                </TableCell>

                                <TableCell>
                                    {screen.row_count}
                                </TableCell>

                                <TableCell>
                                    {screen.col_count}
                                </TableCell>

                                <TableCell align="right">
                                    <IconButton
                                        onClick={() =>
                                            openEditDialog(screen)
                                        }
                                    >
                                        <EditIcon fontSize="small" />
                                    </IconButton>

                                    <IconButton
                                        onClick={() =>
                                            setDeleteTarget(screen)
                                        }
                                    >
                                        <DeleteIcon fontSize="small" />
                                    </IconButton>
                                </TableCell>
                            </TableRow>
                        ))}

                        {screens.length === 0 && (
                            <TableRow>
                                <TableCell
                                    colSpan={5}
                                    align="center"
                                >
                                    登録されているスクリーンがありません。
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
                        ? 'スクリーン情報の編集'
                        : 'スクリーンの新規登録'}
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
                        select
                        label="劇場"
                        value={form.theater}
                        onChange={(e) =>
                            handleChange(
                                'theater',
                                e.target.value
                            )
                        }
                        required
                        fullWidth
                    >
                        {theaters.map((theater) => (
                            <MenuItem
                                key={theater.id}
                                value={theater.id}
                            >
                                {theater.name}
                            </MenuItem>
                        ))}
                    </TextField>

                    <TextField
                        label="スクリーン名"
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
                        label="座席の行数"
                        type="number"
                        value={form.row_count}
                        onChange={(e) =>
                            handleChange(
                                'row_count',
                                e.target.value
                            )
                        }
                        required
                        fullWidth
                    />

                    <TextField
                        label="座席の列数"
                        type="number"
                        value={form.col_count}
                        onChange={(e) =>
                            handleChange(
                                'col_count',
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
                    スクリーンの削除
                </DialogTitle>

                <DialogContent>
                    <Typography>
                        「{deleteTarget?.theater_name} / {deleteTarget?.name}」
                        を削除します。よろしいですか？
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