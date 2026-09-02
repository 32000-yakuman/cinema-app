'use client'

import axios from "../../../plugins/axios"
import {
    AppBar,
    Box,
    Drawer,
    IconButton,
    List,
    ListItemButton,
    ListItemText,
    Toolbar,
    Typography,
} from "@mui/material";
import MenuIcon from '@mui/icons-material/Menu'
import Link from 'next/link'
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const drawerWidth = 220

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const router = useRouter()
    const [checking, setChecking] = useState(true)
    const [mobileOpen, setMobileOpen] = useState(false)

    useEffect(() => {
        axios
            .get("/api/cinema/me/")
            .then((res) => {
                if (!res.data.is_staff) {
                    router.replace("/cinema/movies/")
                    return
                }

                setChecking(false)
            })
            .catch(() => {
                router.replace("/login")
            })
    }, [router])

    if (checking) {
        return null
    }

    const handleDrawerToggle = () => {
        setMobileOpen((prev) => !prev)
    }

     const navItems = [
        { label: 'ダッシュボード', href: '/cinema/admin' },
        { label: '映画管理', href: '/cinema/admin/movies' },
        { label: 'スクリーン管理', href: '/cinema/admin/screens' },
        { label: '上映回管理', href: '/cinema/admin/showtimes' },
        { label: 'ユーザー管理', href: '/cinema/admin/users' },
        { label: '予約管理', href: '/cinema/admin/reservations' },
    ]

    const drawerContent = (
        <>
            <Toolbar>
                <Typography variant="h6">
                    Cinema Admin
                </Typography>
            </Toolbar>

            <List>
                {navItems.map((item) => (
                    <ListItemButton
                        key={item.href}
                        component={Link}
                        href={item.href}
                        onClick={() => setMobileOpen(false)}
                    >
                        <ListItemText primary={item.label} />
                    </ListItemButton>
                ))}
            </List>
        </>
    )

    return (
        <Box sx={{ display: "flex" }}>
            {/* スマホ用: 上部にハンバーガーメニュー付きバー */}
            <AppBar
                position="fixed"
                sx={{
                    display: { mobile: 'block', desktop: 'none' },
                    width: '100%',
                }}
            >
                <Toolbar>
                    <IconButton
                        color="inherit"
                        edge="start"
                        onClick={handleDrawerToggle}
                        sx={{ mr: 2 }}
                    >
                        <MenuIcon />
                    </IconButton>
                    <Typography variant="h6" noWrap>
                        Cinema Admin
                    </Typography>
                </Toolbar>
            </AppBar>

            {/* スマホ用: 開閉式(temporary)Drawer */}
            <Drawer
                variant="temporary"
                open={mobileOpen}
                onClose={handleDrawerToggle}
                ModalProps={{ keepMounted: true }}
                sx={{
                    display: { mobile: 'block', desktop: 'none' },
                    '& .MuiDrawer-paper': {
                        width: drawerWidth,
                        boxSizing: 'border-box',
                    },
                }}
            >
                {drawerContent}
            </Drawer>

            {/* PC用: 常時表示(permanent)Drawer */}
            <Drawer
                variant="permanent"
                sx={{
                    display: { mobile: 'none', desktop: 'block' },
                    width: drawerWidth,
                    '& .MuiDrawer-paper': {
                        width: drawerWidth,
                        boxSizing: 'border-box',
                    },
                }}
            >
                {drawerContent}
            </Drawer>
            
            <Box 
                component="main" 
                sx={{
                    flexGrow: 1,
                    p: 3,
                }}
            >
                <Toolbar />
                {children}
            </Box>
        </Box>
    );
}