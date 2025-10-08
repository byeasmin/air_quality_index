# import pandas as pd
# from fastapi import FastAPI, HTTPException, Query


# df = pd.read_csv("Dhaka_PM2.5_2022.csv")


# df["Date (LT)"] = pd.to_datetime(df["Date (LT)"], format="%d/%m/%Y %H:%M")

# app = FastAPI(title="Air Quality Index API")

# @app.get("/air_quality_index")
# def get_air_quality(
#     date: str = Query(..., description="Date in YYYY-MM-DD format"),
#     hour: int = Query(..., ge=0, le=23, description="Hour in 24-hour format")
# ):
#     try:
        
#         query_date = pd.to_datetime(date)

   
#         row = df[(df["Date (LT)"].dt.date == query_date.date()) & (df["Hour"] == hour)]

#         if row.empty:
#             raise HTTPException(status_code=404, detail="No AQI data for given date/hour")

#         record = row.iloc[0]

#         return {
#             "date": str(record["Date (LT)"].date()),
#             "hour": int(record["Hour"]),
#             "pm25_concentration": float(record["Raw Conc."]),
#             "unit": record["Conc. Unit"],
#             "aqi": int(record["AQI"]),
#             "category": record["AQI Category"],
#             "qc_status": record["QC Name"],
#             "data_source": "Local monitoring dataset"
#         }

#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))







import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


df = pd.read_csv("Dhaka_PM2.5_2022.csv")


df["Date (LT)"] = pd.to_datetime(df["Date (LT)"], format="%d/%m/%Y %H:%M")

app = FastAPI(title="Air Quality Index API")



# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# US EPA PM2.5 Breakpoints
pm25_breakpoints = [
    (0.0, 12.0, 0, 50, "Good"),
    (12.1, 35.4, 51, 100, "Moderate"),
    (35.5, 55.4, 101, 150, "Unhealthy for Sensitive Groups"),
    (55.5, 150.4, 151, 200, "Unhealthy"),
    (150.5, 250.4, 201, 300, "Very Unhealthy"),
    (250.5, 500.4, 301, 500, "Hazardous"),
]


def compute_aqi_pm25(conc: float):
    """Compute AQI from PM2.5 concentration using EPA breakpoints"""
    for c_low, c_high, i_low, i_high, category in pm25_breakpoints:
        if c_low <= conc <= c_high:
            aqi = ((i_high - i_low) / (c_high - c_low)) * (conc - c_low) + i_low
            return round(aqi), category
    return None, "Out of Range"


@app.get("/air_quality_index")
def get_air_quality(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    hour: int = Query(..., ge=0, le=23, description="Hour in 24-hour format")
):
    try:
  
        query_date = pd.to_datetime(date)

        row = df[(df["Date (LT)"].dt.date == query_date.date()) & (df["Hour"] == hour)]

        if row.empty:
            raise HTTPException(status_code=404, detail="No AQI data for given date/hour")

        record = row.iloc[0]
        pm25 = float(record["Raw Conc."])

        aqi, category = compute_aqi_pm25(pm25)

        return {
            "date": str(record["Date (LT)"].date()),
            "hour": int(record["Hour"]),
            "pm25_concentration": pm25,
            "unit": record["Conc. Unit"],
            "aqi": aqi,
            "category": category,
            "qc_status": record["QC Name"],
            "data_source": "Local monitoring dataset"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
