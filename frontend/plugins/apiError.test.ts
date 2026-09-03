import { describe, expect, it } from "vitest"
import axios, { AxiosHeaders } from "axios"
import { getApiErrorMessage } from "./apiError"

describe("getApiErrorMessage", () => {

    // ① errMsg が返ってきた場合
    it("errMsg が存在する場合は errMsg を返す", () => {
        const error = new axios.AxiosError(
            "Request failed",
            "400",
            undefined,
            undefined,
            {
                status: 400,
                statusText: "Bad Request",
                headers: new AxiosHeaders(),
                config: {
                    headers: new AxiosHeaders(),
                },
                data: {
                    errMsg: "予約のキャンセルに失敗しました。",
                },
            }
        )

        const result = getApiErrorMessage(
            error,
            "予約のキャンセルに失敗しました。"
        )

        expect(result).toBe("予約のキャンセルに失敗しました。")
    })


    // ② detail が返ってきた場合
    it("detail が存在する場合は detail を返す", () => {
        const error = new axios.AxiosError(
            "Request failed",
            "400",
            undefined,
            undefined,
            {
                status: 400,
                statusText: "Bad Request",
                headers: new AxiosHeaders(),
                config: {
                    headers: new AxiosHeaders(),
                },
                data: {
                    detail: "ポイント残高が不足しています。",
                },
            }
        )

        const result = getApiErrorMessage(
            error,
            "決済に失敗しました。"
        )

        expect(result).toBe("ポイント残高が不足しています。")
    })


    // ③ errMsg / detail が存在しない場合
    it("errMsg と detail がない場合は fallback を返す", () => {
        const error = new axios.AxiosError(
            "Request failed",
            "400",
            undefined,
            undefined,
            {
                status: 400,
                statusText: "Bad Request",
                headers: new AxiosHeaders(),
                config: {
                    headers: new AxiosHeaders(),
                },
                data: {
                    foo: "bar",
                },
            }
        )

        const result = getApiErrorMessage(
            error,
            "予約のキャンセルに失敗しました。"
        )

        expect(result).toBe("予約のキャンセルに失敗しました。")
    })


    // ④ response 自体が存在しない場合
    it("response がないネットワークエラーの場合は fallback を返す", () => {
        const error = new axios.AxiosError(
            "Network Error"
        )

        const result = getApiErrorMessage(
            error,
            "サーバーとの通信に失敗しました。"
        )

        expect(result).toBe("サーバーとの通信に失敗しました。")
    })
})
