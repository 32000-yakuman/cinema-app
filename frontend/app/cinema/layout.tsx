'use client'

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import {
    createTheme,
    AppBar,
    Box,
    Button,
    Divider,
    Drawer,
    IconButton,
    List,
    ListItem,
    ListItemButton,
    ListItemText,
    ThemeProvider,
    Toolbar,
    Typography,
} from "@mui/material";
import { Logout as LogoutIcon, Menu as MenuIcon, MovieSharp } from "@mui/icons-material"
import axios from "../../plugins/axios"

const defaultTheme = createTheme ({
    breakpoints: {
        values: {
            mobile: 0,
            desktop: 600,
        },
    },
})

type Movie = {
    id: number;
    title: string;
}

export default function CinemaLayout({ children } : { children: React.ReactNode }) {
    const [open, setOpen] = useState(false)
    const [isLoggedIn, setIsLoggedIn] = useState(false)
    const [movies, setMovies] = useState<Movie[]>([])
    const router = useRouter()

    // 🔥 Django にログイン状態を問い合わせる
    useEffect(() => {
        axios
            .get("/api/cinema/me/", { withCredentials: true })
            .then(() => setIsLoggedIn(true))
            .catch(() => setIsLoggedIn(false))
    }, [])

    // 上映中の映画一覧の取得
    useEffect(() => {
        axios
            .get("/api/cinema/movies/")
            .then((res) => setMovies(res.data))
            .catch(() => setMovies([]))
    }, [])

    const handleLogin = () => {
        router.replace('/login')
    }
    
    const handleLogout = async () => {
        try {
            await axios.post("/api/cinema/logout/")
        } finally {
            router.replace('/cinema/movies')
        }
    }

    const toggleDrawer = (open: boolean) => {
        setOpen(open)
    }

    const list = () => (
        <Box sx={{ width: 240 }}>
            <Toolbar />
            <Divider />
            <List>
                <ListItem component="a" href="/cinema/mypage/" disablePadding>
                    <ListItemButton>
                        <ListItemText primary="マイページ" />
                    </ListItemButton>
                </ListItem>
                <ListItem component="a" href="/cinema/reservations/" disablePadding>
                    <ListItemButton>
                        <ListItemText primary="予約履歴" />
                    </ListItemButton>
                </ListItem>
                <ListItem component="a" href="/cinema/movies/" disablePadding>
                    <ListItemButton>
                        <ListItemText primary="上映中の映画一覧" />
                    </ListItemButton>
                </ListItem>
                <Divider />
                {movies.map((movie) => (
                    <ListItem key={movie.id} component="a" href={`/cinema/movies/${movie.id}/showtimes/`} disablePadding>
                        <ListItemButton>
                            <ListItemText primary={movie.title} />
                        </ListItemButton>
                    </ListItem>
                ))}
                <Divider />
            </List>
        </Box>
    )

    return(
        <ThemeProvider theme={defaultTheme}>
            <Box sx={{ display: "flex"}}>
                <AppBar position="fixed">
                    <Toolbar>
                        <IconButton onClick={() => toggleDrawer(true)}>
                            <MenuIcon />
                        </IconButton>
                        <Typography 
                            variant="h6"
                            noWrap
                            component="div"
                            sx={{ flexGrow: 1 }}
                        >
                            秘封映画館
                        </Typography>
                        
                        {/* 🔥 ログイン状態でボタンを切り替え */}
                        {isLoggedIn ? (
                            <Button
                                variant="contained"
                                startIcon={<LogoutIcon />}
                                onClick={handleLogout}
                            >
                                ログアウト
                            </Button>
                        ) : (
                            <Button
                                variant="contained"
                                onClick={handleLogin}
                            >
                                ログイン
                            </Button>
                        )}
                    </Toolbar>
                </AppBar>

                <Drawer open={open} onClose={() => toggleDrawer(false)} anchor="left">
                    {list()}
                </Drawer>

                <Box
                    component="main"
                    sx={{
                        flexGrow: 1,
                        p: 3,
                        marginTop: "64px",
                        width: '100%',
                        background: "white",
                    }}
                >
                    {children}
                </Box>

                <Box
                    component='footer'
                    sx={{
                        width: '100%',
                        position: 'fixed',
                        textAlign: 'center',
                        bottom: 0,
                        background: "#1976b2",
                    }}
                >
                    <Typography variant="caption" color="white">
                        2023 full stack web development
                    </Typography>
                </Box>
            </Box>
        </ThemeProvider>
    )
}
