'use client'

import axios from "../../../plugins/axios"
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    Divider,
    Snackbar,
    Stack,
    Typography,
} from "@mui/material"
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { getApiErrorMessage } from "../../../plugins/apiError"

type ReservationSeat = {
    id: number
    seat: number
    seat_label: string
    showtime: number
    price: number
}

type Reservation = {
    id: number
    showtime: number
    movie_title: string
    screen_name: string
    start_time: string
    end_time: string
    status: string
    status_display: string
    reserved_at: string
    total_price: number
    seats: ReservationSeat[]
    payment_status: string | null
    payment_status_display: string
    expires_at: string | null;
}

export default function ReservationsPage() {
    const router = useRouter()

    const [reservations, setReservations] = useState<Reservation[]>([])
    const [errorMessage, setErrorMessage] = useState("")
    const [successMessage, setSuccessMessage] = useState("")
    const [loading, setLoading] = useState(true)

    const fetchReservations = () => {
        setLoading(true)

        axios
            .get("/api/cinema/reservations/")
            .then((res) => {
                setReservations(res.data)
            })
            .catch((err) => {
                setErrorMessage(
                    getApiErrorMessage(err, "予約履歴の取得に失敗しました。")
                )
            })
            .finally(() => {
                setLoading(false)
            })
    }

    useEffect(() => {
        fetchReservations()
    }, [])

    const handleCancel = (reservation: Reservation) => {
        if (
            !window.confirm(
                `予約番号 ${reservation.id} をキャンセルしますか？\n\nこの操作は元に戻せません。`
            )
        ) {
            return
        }

        axios
            .post(
                `/api/cinema/reservations/${reservation.id}/cancel/`
            )
            .then(() => {
                setSuccessMessage("予約をキャンセルしました。")
                fetchReservations()
            })
            .catch((err) => {
                setErrorMessage(
                    getApiErrorMessage(err, "予約のキャンセルに失敗しました。")
                )
            })
    }

    const getReservationStatusColor = (
        status: string
    ): "success" | "warning" | "default" => {
        switch (status) {
            case "confirmed":
                return "success"

            case "pending":
                return "warning"

            case "cancelled":
                return "default"

            default:
                return "default"
        }
    }

    const getPaymentStatusColor = (
        status: string | null
    ): "success" | "warning" | "default" => {
        switch (status) {
            case "confirmed":
                return "success"

            case "pending":
                return "warning"

            case "cancelled":
                return "default"

            default:
                return "default"
        }
    }

    const formatDateTime = (value: string) => {
        const date = new Date(value)

        return date.toLocaleString("ja-JP", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            weekday: "short",
            hour: "2-digit",
            minute: "2-digit",
        })
    }

    const formatPrice = (price: number) => {
        return `${price.toLocaleString("ja-JP")}円`
    }

    const formatSeats = (seats: ReservationSeat[]) => {
        if (!seats || seats.length === 0) {
            return "-"
        }

        return seats
             .map((reservationSeat) => reservationSeat.seat_label)
            .join("、")
    }

    const canCancel = (reservation: Reservation) => {
        return reservation.status !== "cancelled"
    }

    const canPay = (reservation: Reservation) => {
        return (
            reservation.status !== "cancelled" &&
            reservation.payment_status === null
        )
    }

    if (loading) {
        return (
            <Box>
                <Typography variant="h5" sx={{ mb: 3 }}>
                    予約履歴
                </Typography>

                <Typography>
                    予約履歴を読み込んでいます...
                </Typography>
            </Box>
        )
    }

    return (
        <Box>
            <Typography variant="h5" sx={{ mb: 3 }}>
                予約履歴
            </Typography>

            {reservations.length === 0 ? (
                <Card>
                    <CardContent>
                        <Typography
                            variant="body1"
                            align="center"
                            sx={{ py: 4 }}
                        >
                            予約履歴はありません。
                        </Typography>

                        <Box sx={{ textAlign: "center" }}>
                            <Button
                                variant="contained"
                                onClick={() =>
                                    router.push("/cinema/movies/")
                                }
                            >
                                映画を探す
                            </Button>
                        </Box>
                    </CardContent>
                </Card>
            ) : (
                <Stack spacing={2}>
                    {reservations.map((reservation) => (
                        <Card key={reservation.id}>
                            <CardContent>
                                <Typography
                                    variant="h6"
                                    sx={{ mb: 1 }}
                                >
                                    {reservation.movie_title}
                                </Typography>

                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                    sx={{ mb: 2 }}
                                >
                                    予約番号：{reservation.id}
                                </Typography>

                                <Divider sx={{ mb: 2 }} />

                                <Stack spacing={1.5}>
                                    <Box>
                                        <Typography
                                            variant="body2"
                                            color="text.secondary"
                                        >
                                            上映日時
                                        </Typography>

                                        <Typography variant="body1">
                                            {formatDateTime(
                                                reservation.start_time
                                            )}
                                            {" ～ "}
                                            {new Date(
                                                reservation.end_time
                                            ).toLocaleTimeString(
                                                "ja-JP",
                                                {
                                                    hour: "2-digit",
                                                    minute: "2-digit",
                                                }
                                            )}
                                        </Typography>
                                    </Box>

                                    <Box>
                                        <Typography
                                            variant="body2"
                                            color="text.secondary"
                                        >
                                            スクリーン
                                        </Typography>

                                        <Typography variant="body1">
                                            {reservation.screen_name}
                                        </Typography>
                                    </Box>

                                    <Box>
                                        <Typography
                                            variant="body2"
                                            color="text.secondary"
                                        >
                                            座席
                                        </Typography>

                                        <Typography variant="body1">
                                            {formatSeats(
                                                reservation.seats
                                            )}
                                        </Typography>
                                    </Box>

                                    <Box>
                                        <Typography
                                            variant="body2"
                                            color="text.secondary"
                                            sx={{ mb: 0.5 }}
                                        >
                                            予約状態
                                        </Typography>

                                        <Chip
                                            label={
                                                reservation.status_display
                                            }
                                            color={getReservationStatusColor(
                                                reservation.status
                                            )}
                                            size="small"
                                        />
                                    </Box>

                                    <Box>
                                        <Typography
                                            variant="body2"
                                            color="text.secondary"
                                            sx={{ mb: 0.5 }}
                                        >
                                            決済状態
                                        </Typography>

                                        <Chip
                                            label={
                                                reservation.payment_status_display
                                            }
                                            color={getPaymentStatusColor(
                                                reservation.payment_status
                                            )}
                                            size="small"
                                        />
                                    </Box>

                                    <Box>
                                        <Typography
                                            variant="body2"
                                            color="text.secondary"
                                        >
                                            合計金額
                                        </Typography>

                                        <Typography
                                            variant="h6"
                                            sx={{ mt: 0.5 }}
                                        >
                                            {formatPrice(
                                                reservation.total_price
                                            )}
                                        </Typography>
                                    </Box>
                                </Stack>

                                <Divider sx={{ my: 2 }} />

                                <Stack
                                    direction="row"
                                    spacing={1}
                                    sx={{ flexWrap: "wrap" }}
                                    useFlexGap
                                >
                                    <Button
                                        variant="outlined"
                                        onClick={() =>
                                            router.push(
                                                `/cinema/reservations/${reservation.id}/`
                                            )
                                        }
                                    >
                                        予約詳細
                                    </Button>

                                    {canPay(reservation) && (
                                        <Button
                                            variant="contained"
                                            color="primary"
                                            onClick={() =>
                                                router.push(
                                                    `/cinema/reservations/${reservation.id}/payment/`
                                                )
                                            }
                                        >
                                            支払いへ
                                        </Button>
                                    )}

                                    {canCancel(reservation) && (
                                        <Button
                                            variant="outlined"
                                            color="error"
                                            onClick={() =>
                                                handleCancel(reservation)
                                            }
                                        >
                                            キャンセル
                                        </Button>
                                    )}
                                </Stack>
                            </CardContent>
                        </Card>
                    ))}
                </Stack>
            )}

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

            <Snackbar
                open={!!successMessage}
                autoHideDuration={3000}
                onClose={() => setSuccessMessage("")}
            >
                <Alert
                    severity="success"
                    onClose={() => setSuccessMessage("")}
                >
                    {successMessage}
                </Alert>
            </Snackbar>
        </Box>
    )
}