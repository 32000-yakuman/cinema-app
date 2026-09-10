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
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { useForm } from "react-hook-form"
import { Suspense, useState } from 'react';

type FormData = {
    username: string;
    password: string;
};

function LoginForm() {   
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<FormData>();
    const [authError, setAuthError] = useState<string | null>(null)
    const router = useRouter()
    const serchParams = useSearchParams()
    const justRegistered = serchParams.get("registered") === "true"


    const defaultTheme = createTheme()

    const onSubmit = (data: FormData): void => {
        handleLogin(data)
    }

    const handleLogin = (data: FormData) => {
        axios_instance
            .post("/api/cinema/login/", data)
            .then(() => axios_instance.get("/api/cinema/me/"))
            .then((res) => {                
                if (res.data.is_staff) {
                  router.push("/cinema/admin/")
                } else if (res.data.is_staff_member) {
                    router.push("/cinema/staff/reservations/")
                } else {
                    router.push("/cinema/movies/")
                }
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
                    {justRegistered && (
                        <Typography 
                            variant="h6"
                            color="info" 
                            sx={{ marginBottom: 2 }}
                        >
                            登録が完了しました。ログインしてください。    
                        </Typography>
                    )}

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

                        <Typography variant="body2">
                            映画一覧は{' '}
                            <Link href="/cinema/movies/">こちら</Link>
                        </Typography>

                        <Typography variant="body2">
                            アカウント作成は{' '}
                            <Link href="/register">こちら</Link>
                        </Typography>

                    </Box>
                </Box>
            </Container>
        </ThemeProvider>
    );
}

export default function Page() {
    return (
        <Suspense fallback={null}>
            <LoginForm />
        </Suspense>
    );
}