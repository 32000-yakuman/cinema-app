'use client'

import axios from "../../../../plugins/axios"
import {
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    Container,
    Divider,
    Typography,
} from '@mui/material';
import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation'


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
}


export default function Page() {
    const params = useParams();
    const router = useRouter();
    const reservationId = params.id;
        
    
    const [reservation, setReservation] = useState<ReservationData | null>(null);

    const fetchReservation = () => {
        axios.get(`/api/cinema/reservations/${reservationId}/`)
            .then((res) => res.data)
            .then((data) => { setReservation(data) })
        }


    useEffect(() => {
        fetchReservation()
    }, [reservationId])
    

    const handleCancel = () => {
        axios.post(`/api/cinema/reservations/${reservationId}/cancel/`)    
            .then(() => {
                fetchReservation()
            })
    }


    if (!reservation) {
        return (
            <Container sx={{ marginTop: 4 }}>
                <Typography>読み込み中...</Typography>    
            </Container>
        )
    }


    return (
        <Container sx={{ marginTop: 4 }}>
            <Typography variant="h5" gutterBottom>
                ご予約内容
            </Typography>        
            <Card>
                <CardContent>
                    <Box>
                        <Typography variant="body2"  color="text.secondary" gutterBottom>
                            予約番号: {reservation.id}
                        </Typography>
                        <Chip 
                            label={reservation.status_display}
                            color={reservation.status === 'cancelled' ? 'default' : 'primary'}
                        />
                    </Box>
                    <Divider sx={{ marginY: 2 }} />
                    <Typography variant="body1" gutterBottom>
                        座席
                    </Typography>
                    {reservation.seats.map((seat) => (
                        <Typography key={seat.id} variant="body2">
                            {seat.seat_label} - {seat.price.toLocaleString()}
                        </Typography>                                 
                    ))}
                    <Divider sx={{ marginY: 2 }} />
                    <Typography variant="h6">
                        合計: {reservation.total_price.toLocaleString()}円
                    </Typography>                    
                </CardContent>
            </Card>

            
            {reservation.status !== 'cancelled' && (
                <Box sx={{ display: "flex", justifyContent: "space-between", width: "100%" }}>
                    <Button variant="outlined" color="error" onClick={handleCancel}>
                        予約をキャンセルする
                    </Button>
                    <Button variant="text" onClick={() => router.push('/cinema/movies')}>
                        映画一覧に戻る    
                    </Button>
                </Box>
            )}
        </Container>
    );
}