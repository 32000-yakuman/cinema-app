'use client'

import axios from "../../../../plugins/axios"
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    Container,
    Snackbar,
    TextField,
    Typography,
} from '@mui/material';
import { useState } from 'react';

type StaffReservationSeat = {
    id: number;
    seat: number;
    seat_label: string;
    showtime: number;
    price: number;
}

type StaffReservation = {
    id: number;
    username: string;
    customer_name: string;
    movie_title: string;
    screen_name: string;
    status: string;
    status_display: string;
    checked_in_at: string | null;
    reserved_at: string;
    total_price: number;
    payment_status: string | null;
    payment_status_display: string;
    seats: Array<StaffReservationSeat>;
}

export default function Page() {
    const [query, setQuery] = useState('')
    const [results, setResults] = useState<Array<StaffReservation>>([])
    const [message, setMessage] = useState('')
    const [errorMessage, setErrorMessage] = useState('')

    const handleSearch = () => {
        axios.get(`/api/cinema/staff/reservations/?query=${encodeURIComponent(query)}`)
            .then((res) => res.data)
            .then((data) => { setResults(data) })
            .catch(() => { setErrorMessage('検索に失敗しました。')})
    }

    const handleConfirmPayment = (reservationId: number) => {
        axios.patch(`/api/cinema/reservations/${reservationId}/payment/confirm/`)
            .then(() => {
                setMessage('決済を確定しました。')
                handleSearch()
            })
            .catch((err) => {
                setErrorMessage(err.response?.data?.errMsg || '決済確定に失敗しました。')
            })
    }

    
    const handleCheckIn = (reservationId: number) => {
        axios.post(`/api/cinema/reservations/${reservationId}/check-in/`)
            .then(() => {
                setMessage('チェックインしました')
                handleSearch()
            })
            .catch((err) => {
                setErrorMessage(err.response?.data?.errMsg || 'チェックインに失敗しました。')
            })
    }


    return (
        <Container sx={{ marginTop: 4 }}>
            <Typography variant="h5" gutterBottom>
                窓口： 予約検索
            </Typography>

            <Box sx={{ display: "flex", gap: 2, marginBottom: 3}}>
                <TextField
                    label="予約番号・ユーザー名・氏名"
                    variant="filled"
                    fullWidth
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleSearch() }}
                />
                <Button variant="contained" onClick={handleSearch}>
                    検索
                </Button>
            </Box>

            {results.map((r) => (
                <Card key={r.id} sx={{ marginBottom: 2 }}>
                    <CardContent>
                        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <Typography variant="subtitle1">
                                予約番号: {r.id} / {r.customer_name}
                            </Typography>
                            <Chip label={r.status_display} size="small" />
                        </Box>

                        <Typography variant="body2" color="text.secondary">
                                {r.movie_title} / {r.screen_name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                                座席: {r.seats.length > 0
                                    ? r.seats.map((s) => s.seat_label).join(', ')
                                : 'なし'} ({r.seats.length}席)
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                                合計: {r.total_price.toLocaleString()}円 / 決済: {r.payment_status_display}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                                チェックイン: {r.checked_in_at ? r.checked_in_at : '未'}
                        </Typography>

                        <Box sx={{ display: "flex", gap: 1, marginTop: 2 }}>
                            <Button
                                variant="outlined"
                                size="small"
                                disabled={r.payment_status !== 'pending'}
                                onClick={() => handleConfirmPayment(r.id)}
                            >
                                決済確定(会計)
                            </Button>
                            <Button
                                variant="outlined"
                                size="small"
                                disabled={!!r.checked_in_at || r.payment_status !== 'confirmed'}
                                onClick={() => handleCheckIn(r.id)}
                            >
                                チェックイン
                            </Button>
                        </Box>
                    </CardContent>
                </Card>
            ))}

            <Snackbar
                open={!!message}
                autoHideDuration={3000}
                onClose={() => setMessage('')}
            >
                <Alert severity="success">{message}</Alert>
            </Snackbar>

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