'use client'

import axios from "../../../../../plugins/axios"
import {getApiErrorMessage} from "../../../../../plugins/apiError"
import {
    Alert,
    Box,
    Button,
    Container,
    Divider,
    Snackbar,
    Typography
} from "@mui/material";
import { useTheme, useMediaQuery } from '@mui/material';
import { CheckCircle } from '@mui/icons-material';
import { useState, useEffect } from 'react';
import { useParams, useRouter } from "next/navigation"
import { relative } from "path";

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

    const rows = Array.from(new Set(seats.map((s) => s.row_label))).sort()
    const maxSeatNumber = seats.length
        ? Math.max(...seats.map((s) => s.seat_number))
        : 0
    const columns = Array.from({ length: maxSeatNumber }, (_, i) => i + 1)

    const theme = useTheme();
    const isXs = useMediaQuery(theme.breakpoints.down('desktop'));

    const seatSize = isXs ? 26 : 32;
    const seatGap = isXs ? 0.5 : 1;
    const labelColWidth = isXs ? 20 : 24;


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
                    setErrorMessage(
                        getApiErrorMessage(
                            err, 
                            '予約内容に誤りがあります。'
                        )
                    )
                } else {
                    setErrorMessage(
                        getApiErrorMessage(
                            err,
                            '予約に失敗しました。もう一度お試しください。'
                        )
                    )
                }
            })
    }

    const totalPrice = showtime ? selectedIds.length * showtime.base_price : 0

    
    return (
        <Container sx={{ marginTop: 2, marginBottom: 10 }}>
            {showtime && (
                <>
                    <Typography variant="h5" gutterBottom>{showtime.movie_title}</Typography>
                    <Typography variant="body2" color="text.secondary">
                        {showtime.theater_name} / {showtime.screen_name}
                    </Typography>
                </>
            )}
            <Divider sx={{ marginY: 1.5}} />

            {/* スクリーン表示 */}
            <Box
                role="img"
                aria-label="スクリーン"
                sx={{
                    width: "80%",
                    maxWidth: 480,
                    height: 8,
                    mx: "auto",
                    mt: 1,
                    borderRadius: "50%",
                    bgcolor: "grey.400",
                    boxShadow: "0 6px 16px rgba(0,0,0,0.2)",
                }}
            />
            <Typography
                align="center"
                variant="caption"
                color="text.secondary"
                sx={{ display: "block", mt: 1, mb: 4, letterSpacing: 4 }}
            >
                SCREEN
            </Typography>
            
            {/*　座席表示 */}
            <Box
                sx={{
                    marginBottom: 2,
                    maxHeight: { xs: "45vh", sm: "55vh" },
                    overflowY: "auto",
                    overflowX: "auto",
                }}
            >
                {/* スクロールヒント(スマホのみ、左右端にグラデーション) */}
                {isXs && (
                    <>
                        <Box
                            sx={{
                                position: "sticky",
                                left: 0,
                                top: 0,
                                height: "100%",
                                width: 16,
                                float: "left",
                                ml: -2,
                                pointerEvents: "none",
                                background: "linear-gradient(to right, rgba(255,255,255,0.9), transparent)",
                                zIndex: 2,
                            }}
                        />
                        <Box
                            sx={{
                                position: "sticky",
                                right: 0,
                                top: 0,
                                height: "100%",
                                width: 16,
                                float: "right",
                                mr: -2,
                                pointerEvents: "none",
                                background: "linear-gradient(to left, rgba(255,255,255,0.9), transparent)",
                                zIndex: 2,
                            }}
                        />
                    </>
                )}
                <Box sx={{
                    // flexでは左詰めに表示されるのでGridで
                    display: "grid",
                    justifyContent: "center",
                    overflowX: "auto",
                    }}
                >
                    <Box
                        sx={{
                            display: "inline-grid",
                            gridTemplateColumns: `${labelColWidth}px repeat(${maxSeatNumber}, ${seatSize}px)`,
                            gap: seatGap,
                            alignItems: "center",                            
                        }}
                    >
                        {/* 列番号ヘッダー */}
                        <Box />  
                        {columns.map((col) => (
                            <Typography 
                                key={`col-${col}`}
                                variant="caption" 
                                align="center" 
                                color="text.secondary"
                            >
                                {col}
                            </Typography>
                        ))}

                        {/* 座席本体 */}
                        {rows.map((row) => (
                            <Box key={`row-${row}`} sx={{ display: "contents"}}> 
                                <Typography sx={{ width:labelColWidth }}>{row}</Typography>
                                {columns.map((col) => {
                                    const seat = seats.find(
                                        (s) => s.row_label === row && s.seat_number === col
                                    )
                                    if (!seat) {
                                        return <Box key={`${row}-${col}`} />
                                    }
                                    return ( 
                                        <Box
                                            key={seat.id}
                                            onClick={() => toggleSeat(seat)}
                                            sx={{
                                                position: "relative",
                                                width: seatSize,
                                                height: seatSize,
                                                display: "flex",
                                                alignItems: "center",
                                                justifyContent: "center",
                                                borderRadius: "8px 8px 4px 4px",
                                                fontSize: isXs ? 10 : 12,
                                                cursor: seat.is_reserved ? "not-allowed" : "pointer",
                                                transition: "all 0.15s ease",
                                                boxShadow: "0 2px 3px rgba(0,0,0,0.25)",
                                                border: "1px solid",
                                                borderColor: "divider",
                                                opacity: seat.is_reserved ? 0.5 : 1,
                                                transform: selectedIds.includes(seat.id) ? "scale(1.05)" : "scale(1)",
                                                zIndex: selectedIds.includes(seat.id) ? 1 : 0,
                                                bgcolor: seat.is_reserved
                                                    ? "grey.400"
                                                    : selectedIds.includes(seat.id)
                                                    ? "primary.main"
                                                    : "grey.100",
                                                backgroundImage: seat.is_reserved
                                                    ? "repeating-linear-gradient(45deg, rgba(0,0,0,0.08) 0px, rgba(0,0,0,0.08) 3px, transparent 3px, transparent 6px)"
                                                    : "none",
                                                color: selectedIds.includes(seat.id) ? "white" : "text.primary",
                                                "&:hover": !seat.is_reserved
                                                    ? { boxShadow: "0 4px 6px rgba(0,0,0,0.25)"}
                                                    : {},
                                            }}
                                        >
                                            {selectedIds.includes(seat.id) ? (
                                                <CheckCircle sx={{ fontSize: isXs ? 12 : 16 }} />
                                            ) : (
                                                seat.seat_number
                                            )}
                                        </Box>
                                    )
                                })}
                            </Box>
                        ))}
                    </Box>
                </Box>
            </Box>

            <Box
                sx={{
                    display: "flex",
                    gap: 3,
                    justifyContent: "center",
                    flexWrap: "wrap",
                    mb: 2,
                }}
            >
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5}}>
                    <Box
                        sx={{
                            width: 20,
                            height: 20,
                            borderRadius: "6px 6px 3px 3px",
                            bgcolor: "grey.100",
                            border: "1px solid",
                            borderColor: "divider",
                        }}
                    />
                    <Typography variant="caption" color="text.secondary">利用可能</Typography>
                </Box>

                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                    <Box
                        sx={{
                            width: 20,
                            height: 20,
                            borderRadius: "6px 6px 3px 3px",
                            bgcolor: "primary.main",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                        }}
                    >
                        <CheckCircle sx={{ fontSize: 14, color: "white" }} />
                    </Box>
                    <Typography variant="caption" color="text.secondary">選択中</Typography>
                </Box>

                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                    <Box
                        sx={{
                            width: 20,
                            height: 20,
                            borderRadius: "6px 6px 3px 3px",
                            bgcolor: "grey.400",
                            opacity: 0.5,
                            backgroundImage:
                                "repeating-linear-gradient(45deg, rgba(0,0,0,0.08) 0px, rgba(0,0,0,0.08) 3px, transparent 3px, transparent 6px)",
                            border: "1px solid",
                            borderColor: "divider",
                        }}
                    />
                    <Typography variant="caption" color="text.secondary">予約済み</Typography>
                </Box>
            </Box>

            <Divider sx={{ marginY: 2}} />

            <Box
                sx={{
                    display: "flex",
                    flexDirection: { xs: "column", sm: "row" },
                    justifyContent: "space-between",
                    alignItems: { xs: "stretch", sm: "center" },
                    gap: { xs: 1.5, sm: 0 },
                }}
            >
                <Typography>
                    選択座席: {selectedIds.length}席　合計: {totalPrice.toLocaleString()}円
                </Typography>
                <Button
                    variant="contained"
                    disabled={selectedIds.length === 0}
                    onClick={handleReserve}
                    fullWidth={isXs}
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