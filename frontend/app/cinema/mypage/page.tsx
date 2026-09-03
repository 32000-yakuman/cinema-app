'use client'

import axios from "../../../plugins/axios"
import { getApiErrorMessage } from "../../../plugins/apiError"
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    Divider,
    Link,
    Snackbar,
    Stack,
    Typography,
} from "@mui/material"
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

type MeData = {
    user_id: number
    username: string
    first_name: string | null
    last_name: string | null
    // 今後使う場面に備えて
    is_staff_member: boolean
    is_staff: boolean
}

type PointData = {
    balance: number
}

const POINT_REDEEM_COST = 5

export default function MyPage() {
    const router = useRouter()

    const [me, setMe] = useState<MeData | null>(null)
    const [pointBalance, setPointBalance] = useState<number | null>(null)
    const [isUnauthorized, setUnauthorized] = useState(false)
    const [errorMessage, setErrorMessage] = useState("")
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchMyPage = async () => {
            setLoading(true)
            setErrorMessage("")

            try {
                const [meRes, pointRes] = await Promise.all([
                    axios.get("/api/cinema/me/"),
                    axios.get("/api/cinema/points/me/"),
                ])

                setMe(meRes.data)
                setPointBalance(pointRes.data.balance)
            } catch (err:any) {
                if (err.response?.status === 401) {
                    setUnauthorized(true)
                    return                
                }

                setErrorMessage(
                    getApiErrorMessage(
                        err,
                        "マイページの情報取得に失敗しました。"
                    )
                )
            } finally {
                setLoading(false)
            }
        }

        fetchMyPage()
    }, [])

    const displayName = (data: MeData) => {
        const name = `${data.last_name} ${data.first_name}`.trim()
        return name
    }

    if (loading) {
        return (
            <Box>
                <Typography variant="h5" sx={{ mb: 3 }}>
                    マイページ
                </Typography>
                <Typography>読み込み中...</Typography>
            </Box>
        )
    }

    // 未ログイン時
    if (isUnauthorized) {
        return (
            <Box>
                <Typography variant="h5" sx={{ mb: 3 }}>
                    マイページ
                </Typography>

                <Alert severity="warning">
                    <Link
                        component="button"
                        underline="hover"
                        onClick={() => router.push("/login")}
                    >
                        ログインしてください。
                    </Link>
                </Alert>
            </Box>
        )
    }


    if (!me) {
        return (
            <Box>
                <Typography variant="h5" sx={{ mb: 3 }}>
                    マイページ
                </Typography>
                <Alert severity="error">{errorMessage}</Alert>
            </Box>
        )
    }

    return (
        <Box>
            <Typography variant="h5" sx={{ mb: 3 }}>
                マイページ
            </Typography>

            <Stack spacing={2}>
                <Card>
                    <CardContent>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            会員情報
                        </Typography>
                        <Divider sx={{ mb: 2 }} />

                        <Stack spacing={1.5}>
                            <Box>
                                <Typography variant="body2" color="text.secondary">
                                    氏名
                                </Typography>
                                <Typography variant="body1">
                                    {displayName(me)}
                                </Typography>
                            </Box>

                            <Box>
                                <Typography variant="body2" color="text.secondary">
                                    ユーザー名
                                </Typography>
                                <Typography variant="body1">
                                    {me.username}
                                </Typography>
                            </Box>
                        </Stack>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            保有ポイント
                        </Typography>
                        <Divider sx={{ mb: 2 }} />

                        <Typography variant="h4" sx={{ mb: 1 }}>
                            {pointBalance}pt
                        </Typography>

                        {pointBalance !== null && pointBalance >= POINT_REDEEM_COST ? (
                            <Typography variant="body2" color="text.secondary">
                                電子チケット{Math.floor(pointBalance / POINT_REDEEM_COST)}枚分と交換できます
                                ({POINT_REDEEM_COST}pt消費で1枚)
                            </Typography>
                        ) : (
                            <Typography variant="body2" color="text.secondary">
                                電子チケットの交換には{POINT_REDEEM_COST}pt必要です
                                (あと{pointBalance !== null ? POINT_REDEEM_COST - pointBalance : "-"}pt)
                            </Typography>
                        )}
                    </CardContent>
                </Card>

                <Button
                    variant="outlined"
                    onClick={() => router.push("/cinema/reservations/")}
                >
                    予約履歴を見る
                </Button>
            </Stack>

            <Snackbar
                open={!!errorMessage}
                autoHideDuration={4000}
                onClose={() => setErrorMessage("")}
            >
                <Alert 
                    severity="error"
                    onClose={() => setErrorMessage("")}
                >
                    {errorMessage}
                </Alert>
            </Snackbar>
        </Box>
    )
}