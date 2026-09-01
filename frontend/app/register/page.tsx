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
    first_name: string;
    last_name: string;
};

export default function Page() {
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<FormData>();
    const [registerError, setRegisterError] = useState<string | null>(null)
    const router = useRouter()

    const defaultTheme = createTheme()

    const onSubmit = (data: FormData): void => {
        axios_instance
            .post("/api/cinema/register/", data)
            .then(() => {
                router.push("/login?registered=true")
            })
            .catch((err) => {
                const detail = err.response?.data
                if (detail?.username) {
                    setRegisterError(detail.username[0])
                } else if (detail?.password) {
                    setRegisterError(detail.password[0])
                } else {
                    setRegisterError("登録に失敗しました。もう一度お試しください。")
                }
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
                        会員登録
                    </Typography>

                    <Box component="form" onSubmit={handleSubmit(onSubmit)}>
                        {registerError && (
                            <Typography variant="body2" color="error">
                                {registerError}
                            </Typography>
                        )}

                        <TextField
                            type="text"
                            variant="filled"
                            label="ユーザー名(必須)"
                            fullWidth
                            margin="normal"
                            {...register("username", { required: "必須入力です。" })}
                            error={Boolean(errors.username)}
                            helperText={errors.username?.message}
                        />

                        <TextField
                            type="password"
                            variant="filled"
                            label="パスワード(必須)"
                            fullWidth
                            margin="normal"
                            {...register("password", {
                                required: "必須入力です。",
                                minLength: {
                                    value: 8,
                                    message: "8文字以上の文字列にしてください。"
                                },
                            })}
                            error={Boolean(errors.password)}
                            helperText={errors.password?.message}
                        />

                        <TextField
                            type="text"
                            variant="filled"
                            label="姓(任意)"
                            fullWidth
                            margin="normal"
                            {...register("last_name")}
                        />

                        <TextField
                            type="text"
                            variant="filled"
                            label="名(任意)"
                            fullWidth
                            margin="normal"
                            {...register("first_name")}
                        />
                        <Button
                            variant="contained"
                            type="submit"
                            fullWidth
                            sx={{ mt: 3, mb: 2 }}
                        >
                            登録する
                        </Button>
                    </Box>
                </Box>
            </Container>
        </ThemeProvider>
    );
}