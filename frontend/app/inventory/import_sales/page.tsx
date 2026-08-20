'use client'

import { useState, useEffect } from 'react'
import axios from "../../../plugins/axios"
import {
    Alert,
    AlertColor,
    Box,
    Button,
    MenuItem,
    Paper,
    Select,
    Snackbar,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Typography,
} from '@mui/material';
import { MuiFileInput } from 'mui-file-input';

export default function Page() {
    const [open, setOpen] = useState(false)
    const [severity, setSeverity] = useState<AlertColor>('success')
    const [message, setMessage] = useState('')
    const [fileSync, setFileSync] = useState()
    const [fileAsync, setFileAsync] = useState()

    const result = (severity: AlertColor, message: string) => {
        setOpen(true)
        setSeverity(severity)
        setMessage(message)
    }
    
    /** 同期処理 **/
    const onChangeFileSync = (newFile: any) => {
        setFileSync(newFile)
    }
    
    const doAddSync = ((e: any) => {
        if (!fileSync) {
            result('error', 'ファイルを選択してください')
            return
        }
        
        const formData = new FormData();
        formData.append('file', fileSync)
        axios.post(`/api/inventory/sync`, formData)        
        
            .then(function (response) {
                console.log(response)
                result('success', '同期ファイルが登録されました')
            })
            .catch(function(error) {
                console.log(error)
                result('error', '同期ファイルが登録に失敗しました')
            })
    })
    const handleClose = (event: any, reason: any) => {
        if (reason === 'clickaway') return;
            setOpen(false)
    }

    /* 売上数の取得 */
    const [data, setData] = useState<any[]>([])
    const [products, setProducts] = useState<any[]>([])
    const [selectedProduct, setSelectedProduct] = useState('')
    
    useEffect(() => {
        axios.get('/api/inventory/products/')
            .then((res) => {
                setProducts(res.data)
            })
            .catch((error) => {
                console.error(error)
            })
    }, [])

    useEffect(() => {
        if (!selectedProduct) {
            setData([])
            return
        }

        axios.get('/api/inventory/summary/', {
            params: {
                product: selectedProduct
            }
        })
            .then((res) => {setData(res.data)})
            .catch((error) => {console.error(error)})
    }, [selectedProduct, open])

    /** 非同期処理 **/
    const onChangeFileAsync = (newFile: any) => {
        setFileAsync(newFile)
    }
    
    const doAddAsync = ((e: any) => {
        if (!fileAsync) {
            result('error', 'ファイルを選択してください')
            return
        }

        const formData = new FormData();
        formData.append('file', fileAsync)
        axios.post(`/api/inventory/async`, formData)        
            .then(function (response) {
                console.log(response)
                result('success', '同期ファイルが登録されました')
            })
            .catch(function(error) {
                console.log(error)
                result('error', '同期ファイルが登録に失敗しました')
            })
    })

    return (
        <Box>
            <Snackbar open={open} autoHideDuration={3000} onClose={handleClose}>
                <Alert severity={severity}>{message}</Alert>
            </Snackbar>
            <Typography variant='h5'>売上一括登録</Typography>
            <Box sx={{ m: 2 }}>
                <Typography variant='subtitle1'>同期でファイル取込</Typography>
                <MuiFileInput value={fileSync} onChange={onChangeFileSync} />
                <Button variant="contained" onClick={doAddSync}>登録</Button>
            </Box>
            
            <Box sx={{ m: 2 }}>
                <Typography variant='subtitle1'>
                    商品を選択
                </Typography>

                <Select
                    value={selectedProduct}
                    onChange={(e) => setSelectedProduct(e.target.value)}
                    displayEmpty
                    sx={{ minWidth: 300, mb: 2 }}
                >
                    <MenuItem value=''>
                        商品を選択してください
                    </MenuItem>

                    {products.map((product) => (
                        <MenuItem
                            key={product.id}
                            value={product.id}
                        >
                         {product.id}:{product.name}
                        </MenuItem>
                    ))}
                </Select>

                <Typography variant='subtitle1'>年月ごとの売上数集計</Typography>
                
                {selectedProduct && (
                    <TableContainer component={Paper}>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>処理月</TableCell>
                                    <TableCell>合計数量</TableCell>
                                </TableRow>
                            </TableHead>

                            <TableBody>
                                {data.map((item: any) => (
                                    <TableRow key={item.monthly_date}>
                                        <TableCell>{item.monthly_date}</TableCell>
                                        <TableCell>{item.monthly_price}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                )}
            </Box>
            <Box sx={{ m: 2 }}>
                <Typography variant='subtitle1'>非同期でファイル取込</Typography>
                <MuiFileInput value={fileAsync} onChange={onChangeFileAsync} />
                <Button variant="contained" onClick={doAddAsync}>登録</Button>
            </Box>
        </Box>
    )
}