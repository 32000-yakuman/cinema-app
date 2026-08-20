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
import { Logout as LogoutIcon, Menu as MenuIcon } from "@mui/icons-material"
import axios from "../../plugins/axios"

const defaultTheme = createTheme ({
    breakpoints: {
        values: {
            mobile: 0,
            desktop: 600,
        },
    },
})

export default function InventoryLayout({ children } : { children: React.ReactNode }) {
    const [open, setOpen] = useState(false)
    const [isLoggedIn, setIsLoggedIn] = useState(false)
    const router = useRouter()

    // 🔥 Django にログイン状態を問い合わせる
    useEffect(() => {
        axios
            .get("/api/inventory/me/", { withCredentials: true })
            .then(() => setIsLoggedIn(true))
            .catch(() => setIsLoggedIn(false))
    }, [])

    const handleLogin = () => {
        router.replace('/login')
    }
    
    const handleLogout = async () => {
        try {
            await axios.post("/api/inventory/logout/")
        } finally {
            router.replace('/login')
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
                <ListItem component="a" href="/inventory/products" disablePadding>
                    <ListItemButton>
                        <ListItemText primary="商品一覧" />
                    </ListItemButton>
                </ListItem>
                <Divider />
                <ListItem component="a" href="/inventory/import_sales" disablePadding>
                    <ListItemButton>
                        <ListItemText primary="売上一括登録" />
                    </ListItemButton>
                </ListItem>
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
                            在庫管理システム
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
