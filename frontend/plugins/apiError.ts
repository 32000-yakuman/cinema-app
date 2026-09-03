import axios from "axios"

// 共通エラー取得関数
export const getApiErrorMessage = (
    error: unknown,
    fallback: string
): string => {
    if (axios.isAxiosError(error)) {
        const data = error.response?.data

        if (typeof data?.errMsg === "string") {
            return data.errMsg
        }

        if (typeof data?.detail === "string") {
            return data.detail
        }
    }

    return fallback
}
