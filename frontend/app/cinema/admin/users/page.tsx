'use client'

import axios from "../../../../plugins/axios"
import {
    Alert,
    Box,
    Button,
    Paper,
    Snackbar,
    Switch,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Typography,
} from "@mui/material"
import { useEffect, useState } from "react"

type AdminUser = {
    id: number
    username: string
    first_name: string
    last_name: string
    date_joined: string
    is_active: boolean
    is_staff_member: boolean
    is_staff: boolean
}

export default function AdminUsersPage() {
    const [users, setUsers] = useState<Array<AdminUser>>([])
    const [errorMessage, setErrorMessage] = useState('')
    const [successMessage, setSuccessMessage] = useState('')
    const [currentUserId, setCurrentUserId] = useState<number | null>(null)

    const fetchUsers = () => {
        axios
            .get('/api/cinema/admin/users/')
            .then((res) => setUsers(res.data))
            .catch(() => setErrorMessage('ユーザー一覧の取得に失敗しました。'))
    }

    useEffect(() => {
        axios
        .get('/api/cinema/me/')
        .then((res) => {
            setCurrentUserId(res.data.user_id)
        })
        .catch(() => {
            setErrorMessage('ユーザー情報の取得に失敗しました。')
        })

        fetchUsers()
    }, [])

    const toggleFlag = (user: AdminUser, field: 'is_active' | 'is_staff_member' | 'is_staff') => {
        const nextValue = !user[field]

        // 楽観的更新
        setUsers((prev) =>
            prev.map((u) => (u.id === user.id ? { ...u, [field]: nextValue } : u))
        )

        axios
            .patch(`/api/cinema/admin/users/${user.id}/`, { [field]: nextValue })
            .then(() => setSuccessMessage(`${user.username}の権限を更新しました。`))
            .catch((err) => {
                // 失敗時はロールバック
                setUsers((prev) =>
                    prev.map((u) => (u.id === user.id ? { ...u, [field]: user[field] } : u))
                )
                setErrorMessage(err.response?.data?.errMsg || '更新に失敗しました。')
            })
    }

    const deleteUser = (user: AdminUser) => {
        if (!window.confirm(
            `${user.username}を削除しますか？\nこの操作は元に戻せません。`
        )) {
            return;
        }

        axios
            .delete(`/api/cinema/admin/users/${user.id}/`)
            .then(() => {
                setUsers((prev) => prev.filter((u) => u.id !== user.id));
                setSuccessMessage(`${user.username}を削除しました。`);
            })
            .catch((err) => {
                setErrorMessage(
                    err.response?.data?.errMsg || 'ユーザー削除に失敗しました。'
                );
            });
    };

    return (
        <Box>
            <Typography variant="h5" sx={{ mb: 3 }}>ユーザー管理</Typography>

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>ユーザー名</TableCell>
                            <TableCell>氏名</TableCell>
                            <TableCell>登録日</TableCell>
                            <TableCell align="center">有効</TableCell>
                            <TableCell align="center">窓口職員</TableCell>
                            <TableCell align="center">管理者</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {users.map((user) => (
                            <TableRow key={user.id}>
                                <TableCell>{user.username}</TableCell>
                                <TableCell>{`${user.last_name} ${user.first_name}`.trim() || '-'}</TableCell>
                                <TableCell>{user.date_joined.slice(0, 10)}</TableCell>
                                <TableCell align="center">
                                    <Switch
                                        checked={user.is_active}
                                        onChange={() => toggleFlag(user, 'is_active')}
                                    />
                                </TableCell>
                                <TableCell align="center">
                                    <Switch
                                        checked={user.is_staff_member}
                                        onChange={() => toggleFlag(user, 'is_staff_member')}
                                    />
                                </TableCell>
                                <TableCell align="center">
                                    <Switch
                                        checked={user.is_staff}
                                        onChange={() => toggleFlag(user, 'is_staff')}
                                    />
                                </TableCell>
                                <TableCell align="center">
                                    <Button
                                        variant="outlined"
                                        color="error"
                                        size="small"
                                        onClick={() => deleteUser(user)}
                                        disabled={currentUserId === user.id}
                                    >
                                        削除
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                        {users.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={6} align="center">
                                    ユーザーがいません。
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </TableContainer>

            <Snackbar open={!!errorMessage} autoHideDuration={4000} onClose={() => setErrorMessage('')}>
                <Alert severity="error">{errorMessage}</Alert>
            </Snackbar>
            <Snackbar open={!!successMessage} autoHideDuration={3000} onClose={() => setSuccessMessage('')}>
                <Alert severity="success">{successMessage}</Alert>
            </Snackbar>
        </Box>
    )
}