import axios from "axios"

const axios_instance = axios.create({
    withCredentials: true,
    baseURL: '',
})

axios_instance.interceptors.request.use(
    function (config) {
        return config
    },
    function (error) {
        return Promise.reject(error)
    }
)

axios_instance.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config

        // originalRequest が存在しない場合
        if (!originalRequest) {
            return Promise.reject(error)
        }

        // 401以外はそのまま返す
        if (error.response?.status !== 401) {
            return Promise.reject(error)
        }

        // すでにRetry済みの場合
        if (originalRequest._retry) {
            return Promise.reject(error)
        }

        originalRequest._retry = true

        // Login / Logout / Retry はRefresh対象外
        const excludedUrls = [
            "/api/cinema/login/",
            "/api/cinema/logout/",
            "/api/cinema/retry/",
        ]

        if (excludedUrls.includes(originalRequest.url)) {
            return Promise.reject(error)
        }

        try {
            // Refresh Tokenを使用してAccess Tokenを更新
            await axios_instance.post(
                "/api/cinema/retry/",
                {}
            )

            // リフレッシュ成功後、リクエストを再送
            return axios_instance(originalRequest)

        } catch (refreshError) {

            return Promise.reject(refreshError)
        }
    }
)

/**
 * ログアウト処理
 *
 * Django側のLogoutViewを呼び出して
 * access / refresh Cookieを削除する。
 */
export const logout = async () => {
    try {
        await axios_instance.post("/api/cinema/logout/")
    } finally {
        window.location.href = "/cinema/movies"
    }
}

export default axios_instance
