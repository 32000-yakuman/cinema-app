'use client'

import axios from "../../../../../plugins/axios"
import { getApiErrorMessage } from "../../../../../plugins/apiError"
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    Container,
    Divider,
    Snackbar,
    Typography,
} from '@mui/material';
import { useState, useEffect } from 'react';
import { useParams, useRouter } from "next/navigation";

type ReservationSeatData = {
    id: number;
    seat: number;
    seat_label: string;    
    price: number;
}


type ReservationData = {
    id: number;
    showtime: number;
    status: string;
    status_display: string;
    reserved_at: string;
    total_price: number;
    seats: Array<ReservationSeatData>;
    expires_at: string | null;
}

type PointData = {
    balance: number;
}

const POINT_REDEEM_COST = 5

export default function Page() {
    const params = useParams()
    const router = useRouter()
    const reservationId = params.id
    
    const [reservation , setReservation] = useState<ReservationData | null>(null)
    const [pointBalance, setPointBalance] = useState<number | null>(null)
    const [errorMessage, setErrorMessage] = useState('')
    const [submitting, setSubmitting] = useState(false)
    const [remainingSeconds, setRemainingSeconds] = useState<number | null>(null)

    const fetchReservation = () => {
        axios.get(`/api/cinema/reservations/${reservationId}/`)
            .then((res) => res.data)
            .then((data) => { setReservation(data) })
    }

    const fetchPoints = () => {
        axios.get('/api/cinema/points/me/')
            .then((res) => res.data)
            .then((data : PointData) => {setPointBalance(data.balance) })
            .catch(() => { setPointBalance(0) })
    }

    useEffect(() => {
        fetchReservation()
        fetchPoints()
    }, [reservationId])

    const handlePayment = (method: 'cash' | 'point') => {
        setSubmitting(true)
        axios.post(`/api/cinema/reservations/${reservationId}/payment/`, {method})
            .then(() => {
                router.push(`/cinema/reservations/${reservationId}`)
            })
            .catch((err) => {
                setErrorMessage(
                    getApiErrorMessage(
                        err,
                        '決済に失敗しました。もう一度お試しください。'
                    )
                )
                setSubmitting(false)
            })
        }

    const canUsePoints = pointBalance !== null && pointBalance >= POINT_REDEEM_COST

    useEffect(() => {
        if (
            !reservation?.expires_at
            || reservation.status !== 'pending'
        ) {
            setRemainingSeconds(null)
            return
        }

        const updateRemaining = () => {
            const seconds = Math.max(
                0,
                Math.ceil(
                    (
                        new Date(
                            reservation.expires_at
                        ).getTime()
                        - Date.now()
                    ) / 1000
                )
            )

            setRemainingSeconds(seconds)
        }

        updateRemaining()

        const timer = window.setInterval(
            updateRemaining,
            1000
        )

        return () => window.clearInterval(timer)
    }, [
        reservation?.expires_at,
        reservation?.status
    ])

    if (!reservation) {
        return (
            <Container>
                <Typography>読み込み中</Typography>
            </Container>
        )
    }


    return (
        <Container sx={{ marginTop: 4}}>
            <Typography>
                お支払方法の選択
            </Typography>
            <Card sx={{ marginBottom: 3 }}>
                <CardContent>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                        予約番号: {reservation.id}
                    </Typography>
                    <Divider sx={{ marginY: 2 }} />
                    {reservation.seats.map((seat) => (
                        <Typography key={seat.id} variant="body2">
                            {seat.seat_label} - {seat.price.toLocaleString()}円
                        </Typography>
                    ))}
                    <Divider sx={{ marginY: 2 }} />
                    <Typography variant="h6">
                        合計: {reservation.total_price.toLocaleString()}円
                    </Typography>
                </CardContent>
            </Card>

            {remainingSeconds !== null && (
                <Alert
                    severity={
                        remainingSeconds === 0
                            ? "error"
                            : "warning"
                    }
                    sx={{ mb: 2 }}
                >
                    {remainingSeconds === 0
                        ? "予約の有効期限が切れました。"
                        : `この予約はあと${
                            Math.floor(
                                remainingSeconds / 60
                            )
                        }分${
                            remainingSeconds % 60
                        }秒で期限切れになります。`
                    }
                </Alert>
            )}

            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <Button
                    variant="contained"
                    size="large"
                    disabled={
                        submitting
                        || remainingSeconds === 0
                    }
                    onClick={() => handlePayment('cash')}
                >
                    現金で支払う
                </Button>

                <Button
                    variant="outlined"
                    size="large"
                    disabled={submitting 
                        || !canUsePoints
                        || remainingSeconds === 0
                    }
                    onClick={() => handlePayment('point')}
                >
                    ポイントで交換する({POINT_REDEEM_COST}pt消費)
                    {pointBalance !== null && ` / 保有: ${pointBalance}pt`}
                </Button>
            </Box>

            <Snackbar
                open={!!errorMessage}
                autoHideDuration={4000}
                onClose={() => setErrorMessage('')}
            >
                <Alert severity="error">{errorMessage}</Alert>
            </Snackbar>              
        </Container>
    );
}