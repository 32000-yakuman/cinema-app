'use client'

import {
    Box,
    Drawer,
    List,
    ListItemButton,
    ListItemText,
    Toolbar,
    Typography,
} from "@mui/material";
import Link from 'next/link'

const drawerWidth = 220

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <Box sx={{display: "flex" }}>
            <Drawer
                variant="permanent"
                sx={{
                    width: drawerWidth,
                    '& .MuiDrawer-paper': {
                        width: drawerWidth,
                        boxSizing: 'border-box',
                    },
                }}
            >
                <Toolbar>
                    <Typography variant="h6">
                        Cinema Admin
                    </Typography>
                </Toolbar>

                <List>
                    <ListItemButton
                        component={Link}
                        href="/cinema/admin"
                    >
                        <ListItemText primary="ダッシュボード" />
                    </ListItemButton>
                    
                    <ListItemButton
                        component={Link}
                        href="/cinema/admin/movies"
                    >
                        <ListItemText primary="映画管理" />
                    </ListItemButton>

                    <ListItemButton
                        component={Link}
                        href="/cinema/admin/screens"
                    >
                        <ListItemText primary="スクリーン管理" />
                    </ListItemButton>

                    <ListItemButton
                        component={Link}
                        href="/cinema/admin/showtimes"
                    >
                        <ListItemText primary="上映回管理" />
                    </ListItemButton>

                    <ListItemButton
                        component={Link}
                        href="/cinema/admin/users"
                    >
                        <ListItemText primary="ユーザー管理" />
                    </ListItemButton>
                    
                    <ListItemButton
                        component={Link}
                        href="/cinema/admin/reservations"
                    >
                        <ListItemText primary="予約管理" />
                    </ListItemButton>
                </List>
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