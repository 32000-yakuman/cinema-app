'use client'

import axios from "../../../../../plugins/axios"
import {
    Alert,
    Box,
    Button,
    Container,
    Divider,
    Snackbar,
    Typography
} from "@mui/material";
import { useState, useEffect } from 'react';
import { useParams, useRouter } from "next/navigation"

type ShowtimeData = {
    id: number;
    movie_title: string;
    screen: number;    
    screen_name: string;    
    theater_name: string;    
    start_time: string;
    base_price: number;
}


type SeatData = {
    id: number;
    row_label: string;
    seat_number: number;    
    seat_type: string;    
    is_reserved: boolean;
}

export default function Page() {   
    const params = useParams();
    const router = useRouter();
    const showtimeId = params.id;

    const [showtime, setShowtime] = useState<ShowtimeData | null>(null);
    const [seats, setSeats] = useState<Array<SeatData>>([]);
    const [selectedIds, setSelectedIds] = useState<Array<number>>([]);
    const [errorMessage, setErrorMessage] = useState('');

    const fetchShowtimes = () => {
        axios.get(`/api/cinema/showtimes/${showtimeId}`)
            .then((res) => res.data)
            .then((data) => { setShowtime(data) })
    }


    const fetchSeats = (screenId: number) => {
        axios.get(`/api/cinema/seats/?screen=${screenId}&showtime=${showtimeId}`)
            .then((res) => res.data)
            .then((data) => { setSeats(data) })
    }

    useEffect(() => {
        fetchShowtimes()
    }, [showtimeId])

    useEffect(() => {
        if (showtime) {
            fetchSeats(showtime.screen)
        }
    }, [showtime])

    const toggleSeat = (seat: SeatData) => {
        if (seat.is_reserved) {
            return
        }
        setSelectedIds((prev) =>
            prev.includes(seat.id)
                ? prev.filter((id) => id !== seat.id)
                : [...prev, seat.id]
        )
    }

    const rows = Array.from(new Set(seats.map((s) => s.row_label)))

    const handleReserve = () => {
        axios.post('/api/cinema/reservations/', {
            showtime_id: Number(showtimeId),
            seat_ids: selectedIds
        })
            .then((res) => res.data)
            .then((data) => {
                router.push(`/cinema/reservations/${data.id}/payment`)
            })
            .catch((err) => {
                if (err.response?.status === 409) {
                    setErrorMessage('選択した座席は他のお客様が確保しました。座席を選び直してください。')
                    if (showtime){
                        fetchSeats(showtime.screen)
                    }
                    setSelectedIds([])
                } else if (err.response?.status === 400) {
                    setErrorMessage(err.response?.data?.errMsg || '予約内容に誤りがあります。')
                } else {
                    setErrorMessage('予約に失敗しました。もう一度お試しください。')
                }
            })
    }

    const totalPrice = showtime ? selectedIds.length * showtime.base_price : 0

    
    return (
        <Container sx={{ marginTop: 4 }}>
            {showtime && (
                <>
                    <Typography variant="h5" gutterBottom>{showtime.movie_title}</Typography>
                    <Typography variant="body2" color="text.secondary">
                        {showtime.theater_name} / {showtime.screen_name}
                    </Typography>
                </>
            )}
            <Divider sx={{ marginY: 2}} />
            
            <Box sx={{ marginBottom: 3 }}>
                {rows.map((row) => (
                    <Box key={row} sx={{ display: "flex", gap: 1, marginBottom: 1 }}> 
                        <Typography sx={{ width:24 }}>{row}</Typography>
                        {seats
                            .filter((s) => s.row_label === row)
                            .sort((a, b) => a.seat_number - b.seat_number)
                            .map((seat) => (
                                <Box
                                    key={seat.id}
                                    onClick={() => toggleSeat(seat)}
                                    sx={{
                                        width: 32,
                                        height: 32,
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        borderRadius: 1,
                                        fontSize: 12,
                                        cursor: seat.is_reserved ? "not-allowed" : "pointer",
                                        bgcolor: seat.is_reserved
                                            ? "grey.400"
                                            : selectedIds.includes(seat.id)
                                            ? "primary.main"
                                            : "grey.100",
                                        color: selectedIds.includes(seat.id) ? "white" : "text.primary",
                                        border: "1px solid #ccc"
                                    }}
                                >
                                    {seat.seat_number}
                                </Box>
                            ))
                        }
                    </Box>
                ))}
            </Box>
            
            <Divider sx={{ marginY: 2}} />

            <Box sx ={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <Typography>
                    選択座席: {selectedIds.length}席　合計: {totalPrice.toLocaleString()}円
                </Typography>
                <Button
                    variant="contained"
                    disabled={selectedIds.length === 0}
                    onClick={handleReserve}
                >
                    この座席で予約する
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