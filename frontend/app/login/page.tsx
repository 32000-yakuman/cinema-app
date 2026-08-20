'use client'

import axios_instance from "../../plugins/axios"
import {
    createTheme,
    Box,
    Button,
    Container,
    CssBaseline,
    TextField,
    Typography,
    ThemeProvider,
} from "@mui/material";
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { useState } from 'react';

type FormData = {
    username: string;
    password: string;
};

export default function Page() {   
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<FormData>();
    const [authError, setAuthError] = useState<string | null>(null)
    const router = useRouter()

    const defaultTheme = createTheme()

    const onSubmit = (data: FormData): void => {
        handleLogin(data)
    }

    const handleLogin = (data: FormData) => {
        axios_instance
            .post("/api/inventory/login/", data)
            .then(() => {
                router.push("/inventory/products/")
            })
            .catch(() => {
                setAuthError("ユーザー名またはパスワードに誤りがあります。")
            })
    }

    return (
        <ThemeProvider theme={defaultTheme}>
            <Container component="main">
                <CssBaseline />
                <Box
                    sx={{
                        marginTop: 8,
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                    }}
                >
                    <Typography component="h1" variant="h5">
                        ログイン
                    </Typography>

                    <Box component="form" onSubmit={handleSubmit(onSubmit)}>
                        {authError && (
                            <Typography variant="body2" color="error">
                                {authError}
                            </Typography>
                        )}

                        <TextField
                            type="text"
                            id="username"
                            variant="filled"
                            label="ユーザー名（必須）"
                            fullWidth
                            margin="normal"
                            {...register("username", { required: "必須入力です。" })}
                            error={Boolean(errors.username)}
                            helperText={errors.username?.message}
                        />

                        <TextField
                            type="password"
                            id="password"
                            variant="filled"
                            label="パスワード（必須）"
                            autoComplete="current-password"
                            fullWidth
                            margin="normal"
                            {...register("password", {
                                required: "必須入力です。",
                                minLength: {
                                    value: 8,
                                    message: "8文字以上の文字列にしてください。",
                                },
                            })}
                            error={Boolean(errors.password)}
                            helperText={errors.password?.message}
                        />

                        <Button
                            variant="contained"
                            type="submit"
                            fullWidth
                            sx={{ mt: 3, mb: 2 }}
                        >
                            ログイン
                        </Button>
                    </Box>
                </Box>
            </Container>
        </ThemeProvider>
    );
}
