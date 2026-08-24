'use client'

import axios from "../../../../../plugins/axios"
import {
    Box,
    Card,
    Container,
    Divider,
    List,
    ListItemButton,
    Typography,
} from "@mui/material";
import { useState, useEffect } from 'react';
import { useParams, useRouter } from "next/navigation";


type MovieData = {
    id: number;
    title: string;
    duration_minutes: string;
}


type ShowtimeData = {
    id: number;
    movie: number;
    movie_title: string;
    screen: number;    
    screen_name: string;    
    theater_name: string;    
    start_time: string;
    end_time: string;
    base_price: number;
}

export default function Page() {    
    const params = useParams();
    const router = useRouter();
    const movieId = params.id;
    

    const [movie, setMovie] = useState<MovieData | null>(null);
    const [showtimes, setShowtimes] = useState<Array<ShowtimeData>>([]);


    const fetchMovie = () => {
        axios.get(`/api/cinema/movies/${movieId}/`)
            .then((res) => res.data)
            .then((data) => { setMovie(data) })
    }


    const fetchShowtimes = () => {
        axios.get(`/api/cinema/showtimes/?movie=${movieId}`)
            .then((res) => res.data)
            .then((data) => { setShowtimes(data) })
    }
    
    
    useEffect(() => {
        fetchMovie()
        fetchShowtimes()
    }, [movieId])
    

    const handleSelect = (showtimeId: number) => {
        router.push(`/cinema/showtimes/${showtimeId}/seats`)
    };

    const formatDateTime = (isoString: string) => {
        const date = new Date(isoString)
        return date.toLocaleString('ja-JP', {
            month: 'numeric', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit'
        })
    }
    

    return (
        <Container sx={{ marginTop: 4 }}>
            <Typography variant="h4" gutterBottom>
                {movie ? movie.title : '読み込み中...'}
            </Typography>        
            {movie && (
                <Typography variant="body2"  color="text.secondary" gutterBottom>
                    上映時間: {movie.duration_minutes}分
                </Typography>
            )}
            <Divider sx={{ marginY: 2}} />
            <Typography variant="h6" gutterBottom>
                上映スケジュール
            </Typography>
            <Card>
                <List disablePadding>
                    {showtimes.map((showtime) => (
                        <ListItemButton
                            key={showtime.id}
                            onClick={() => handleSelect(showtime.id)}
                            divider
                        >
                            <Box sx={{ display: "flex", justifyContent: "space-between", width: "100%" }}>
                                <Box>
                                    <Typography variant="body1">
                                        {formatDateTime(showtime.start_time)}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        {showtime.theater_name} / {showtime.screen_name}
                                    </Typography>
                                </Box>
                                <Typography variant="body1">
                                    {showtime.base_price.toLocaleString()}円
                                </Typography>
                            </Box>
                        </ListItemButton>
                    ))}
                    {showtimes.length === 0 && (
                        <Typography sx={{ padding: 2 }}>
                            現在、上映予定はありません
                        </Typography>
                    )}
                </List>
            </Card>
        </Container>
    );
}