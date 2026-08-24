'use client'

import axios from "../../../plugins/axios"
import {
    Box,
    Card,
    CardActionArea,
    CardContent,
    Chip,
    Container,
    Grid,
    Typography,
} from "@mui/material";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

type MovieData = {
    id: number;
    title: string;
    description: string;
    duration_minutes: string;
    release_date: string;
    rating: string;
    rating_display: string;
}

export default function Page() {
    const router = useRouter()
    const [movies, setMovies] = useState<Array<MovieData>>([]);

    const fetchMovies = () => {
        axios.get('/api/cinema/movies/')
            .then((res) => res.data)
            .then((data) => { setMovies(data) })
    }

    useEffect(() => {
        fetchMovies()
    }, [])

    const handleSelect = (id: number) => {
        router.push(`/cinema/movies/${id}/showtimes/`)
    }

    return (
        <Container sx={{ marginTop: 4 }}>
            <Typography variant="h4" gutterBottom>
                上映中の映画
            </Typography>
            <Grid container spacing={2}>
                {movies.map((movie) => (                
                    <Grid size={{ mobile: 12, desktop: 4 }} key={movie.id}>
                        <Card>
                            <CardActionArea onClick={() => handleSelect(movie.id)}>
                                <CardContent>
                                    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                        <Typography variant="h6">
                                            {movie.title}
                                        </Typography>
                                        <Chip label={movie.rating_display} size="small" />
                                    </Box>
                                    <Typography variant="body2" color="text.secondary" sx={{ marginTop: 1 }}>
                                        {movie.description}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary" sx={{ marginTop: 1, display: "block" }}>
                                        上映時間: {movie.duration_minutes}
                                    </Typography>
                                </CardContent>
                            </CardActionArea>
                        </Card>
                    </Grid>
                ))}
            </Grid>
        </Container>
    );
}