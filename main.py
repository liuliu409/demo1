from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pandas as pd
import os
import uuid
from typing import List
from fastapi.responses import FileResponse
import re

app = FastAPI()

class ExportOption(BaseModel):
    file_phan_tich: str
    nam: int
    bien_can_xuat: List[str]

class ExportRequest(BaseModel):
    lua_chon_xuat: List[ExportOption] = Field(..., description="Danh sách các tổ hợp cần xuất, mỗi tổ hợp tương ứng với một sheet.")

DATA_DIR = "data"
TEMP_DIR = "temp_exports"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

@app.post("/api/export/excel")
async def export_excel(request: ExportRequest):
    file_id = str(uuid.uuid4())
    file_path = os.path.join(TEMP_DIR, f"export_{file_id}.xlsx")

    try:
        sheets_to_create = []

        for item in request.lua_chon_xuat:
            file_phan_tich = item.file_phan_tich
            nam = item.nam
            bien_can_xuat = item.bien_can_xuat

            data_file_path = os.path.join(DATA_DIR, file_phan_tich)
            if not os.path.exists(data_file_path):
                raise HTTPException(status_code=404, detail=f"File '{file_phan_tich}' không tồn tại.")

            try:
                df = pd.read_parquet(data_file_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Lỗi khi đọc file Parquet: {e}")

            # Lọc theo năm
            df_filtered = df[df['VAR_YEAR'].astype(str).str.strip() == str(nam)]
            print(f"[DEBUG] File: {file_phan_tich} | Năm: {nam} => {len(df_filtered)} dòng sau lọc năm")

            if df_filtered.empty:
                continue

            df_filtered = df_filtered.copy()
            df_filtered['BIEN_CODE'] = df_filtered['VAR_NAME_CODE'].str.extract(r'^(\d+):')

            for bien in bien_can_xuat:
                df_filtered_by_var = df_filtered[df_filtered['BIEN_CODE'] == bien]
                print(f"[DEBUG] --> Biến: {bien} => {len(df_filtered_by_var)} dòng")

                if df_filtered_by_var.empty:
                    # Ghi sheet thông báo không có dữ liệu
                    df_selected = pd.DataFrame({"Thông báo": [f"Không có dữ liệu cho biến '{bien}' trong năm {nam}."]})
                else:
                    # Chọn các cột hợp lệ để xuất
                    so_lieu_cols = [
                        'NUM_POLS', 'NUM_CLAIMS', 'EXPOSURE_PREM', 'CLAIM_PMT',
                        'FREQUENCY', 'SEVERITY', 'AVG_PREMIUM', 'PURE_PREMIUM',
                        'LOSS_RATIO', 'GWP_%', 'SUM_ASSURED', 'AVG_SUM_ASSURED'
                    ]
                    mo_ta_cols = [col for col in df.columns if 'VAR_' in col and col != 'VAR_YEAR']
                    cols_to_export = [col for col in (mo_ta_cols + so_lieu_cols) if col in df_filtered_by_var.columns]
                    df_selected = df_filtered_by_var[cols_to_export]

                # Tạo tên sheet
                match_term = re.search(r'_AC(\d+)_', file_phan_tich)
                dieu_khoan = f"AC{match_term.group(1)}" if match_term else "AC_unknown"

                match_var_code = re.search(r'^(\d+)', bien)
                ma_bien = match_var_code.group(1) if match_var_code else "000"

                sheet_name = f"{nam}_{dieu_khoan}_{ma_bien}"
                sheet_name = re.sub(r'[:\\/?*\[\]]', '_', sheet_name)[:31]

                # Đảm bảo tên sheet không trùng
                existing_names = [s[0] for s in sheets_to_create]
                idx = 1
                original_sheet_name = sheet_name
                while sheet_name in existing_names:
                    sheet_name = f"{original_sheet_name}_{idx}"[:31]
                    idx += 1

                sheets_to_create.append((sheet_name, df_selected))

        if not sheets_to_create:
            raise HTTPException(status_code=500, detail="Không có dữ liệu hợp lệ để xuất. Vui lòng kiểm tra lại năm hoặc biến.")

        # Tạo file Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for sheet_name, df_selected in sheets_to_create:
                df_selected.to_excel(writer, sheet_name=sheet_name, index=False)

        return {
            "status": "success",
            "message": "Đã tạo file Excel thành công.",
            "file_id": file_id
        }

    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Lỗi trong quá trình xử lý: {e}")

@app.get("/api/downloads/{file_id}")
async def download_file(file_id: str):
    file_path = os.path.join(TEMP_DIR, f"export_{file_id}.xlsx")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File không tồn tại.")
    
    return FileResponse(
        file_path,
        filename=f"report_{uuid.uuid4()}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
