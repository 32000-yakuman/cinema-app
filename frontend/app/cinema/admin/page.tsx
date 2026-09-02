'use client'

import axios from "../../../plugins/axios"
import {
    Box,
    Card,
    CardActionArea,
    CardContent,
    Chip,
    Grid,
    Typography,
} from '@mui/material'
import {
    Movie as MovieIcon,
    Theaters as TheatersIcon,
    ViewModule as ScreenIcon,
    Schedule as ShowtimeIcon,
    People as PeopleIcon,
    EventSeat as ReservationIcon,
} from '@mui/icons-material'
import Link from 'next/link'
import { useEffect, useState } from "react"

type AdminCard = {
    title: string;
    description: string;
    href: string;
    icon: React.ReactNode
    implemented: boolean
}

const cards: Array<AdminCard> = [
    {
        title: '映画管理',
        description: '映画情報の登録・編集・削除',
        href: '/cinema/admin/movies',
        icon: <MovieIcon fontSize="large" color="primary" />,
        implemented: true,
    },
    {
        title: '劇場管理',
        description: '劇場の登録・編集・削除',
        href: '/cinema/admin/theaters',
        icon: <TheatersIcon fontSize="large" color="primary" />,
        implemented: true,
    },
    {
        title: 'スクリーン管理',
        description: '劇場・スクリーン・座席の登録',
        href: '/cinema/admin/screens',
        icon: <ScreenIcon fontSize="large" color="primary" />,
        implemented: true,
    },
    {
        title: '上映回管理',
        description: '上映スケジュールの登録・編集',
        href: '/cinema/admin/showtimes',
        icon: <ShowtimeIcon fontSize="large" color="primary" />,
        implemented: true,
    },
    {
        title: 'ユーザー管理',
        description: 'アカウント・権限の管理',
        href: '/cinema/admin/users',
        icon: <PeopleIcon fontSize="large" color="primary" />,
        implemented: true,
    },
    {
        title: '予約管理',
        description: '予約状況の確認・対応',
        href: '/cinema/admin/reservations',
        icon: <ReservationIcon fontSize="large" color="primary" />,
        implemented: true,
    },
]

export default function AdminDashboardPage() {
    const [movieCount, setMovieCount] = useState<number | null>(null)
    const [screenCount, setScreenCount] = useState<number | null>(null)


    useEffect(() => {
        axios
            .get('/api/cinema/movies/')
            .then((res) => setMovieCount(res.data.length))
            .catch(() => setMovieCount(null))

        axios
            .get('/api/cinema/screens/')
            .then((res) => setScreenCount(res.data.length))
            .catch(() => setScreenCount(null))
    }, [])

    return (
        <>
            <Typography variant="h4" gutterBottom>
                管理画面
            </Typography>

            <Typography variant="body1" sx={{ mb: 3 }}>
                Cinemaシステム管理
            </Typography>
            
            <Grid container spacing={2} sx={{ mb: 4 }}>
                <Grid size={{ mobile: 12, desktop: 4 }}>
                    <Card>
                        <CardContent>
                           <Typography variant="body2" color="text.secondary">
                                登録映画数
                            </Typography>
                            <Typography variant="h5">
                                {movieCount === null ? '-' : `${movieCount}本`}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                
                <Grid size={{ mobile: 12, desktop: 4 }}>
                    <Card>
                        <CardContent>
                            <Typography variant="body2" color="text.secondary">
                                登録スクリーン数
                            </Typography>
                            <Typography variant="h5">
                                {screenCount === null ? '-' : `${screenCount}件`}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid container spacing={2}>
                    {cards.map((card) => (
                        <Grid key={card.href} size={{ mobile: 12, desktop: 4 }}>
                            <Card sx={{ opacity: card.implemented ? 1 : 0.6 }}>
                                <CardActionArea
                                    component={card.implemented ? Link : 'div'}
                                    href={card.implemented ? card.href : undefined}
                                    disabled={!card.implemented}
                                    sx={{ height: '100%' }}
                                >
                                    <CardContent>
                                        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                                            {card.icon}
                                            {!card.implemented && (
                                                <Chip label="準備中" size="small" />
                                            )}
                                        </Box>
                                        <Typography variant="h6" sx={{ mt: 1 }}>
                                            {card.title}
                                        </Typography>
                                        <Typography color="text.secondary">
                                            {card.description}
                                        </Typography>
                                    </CardContent>
                                </CardActionArea>
                            </Card>
                        </Grid>
                    ))}
                </Grid>
            </Grid>
        </>
    )
}