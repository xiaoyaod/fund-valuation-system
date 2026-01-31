import akshare as ak
import yfinance as yf
import ccxt
import json
import os
import concurrent.futures
from datetime import datetime
import pytz
import time

# === 全球资产监控清单 ===
ASSETS = [
    # --- 加密货币 (24小时实时) ---
    {"code": "BTC", "name": "比特币", "type": "crypto", "symbol": "BTC/USDT"},
    {"code": "ETH", "name": "以太坊", "type": "crypto", "symbol": "ETH/USDT"},
    {"code": "DOGE", "name": "狗狗币", "type": "crypto", "symbol": "DOGE/USDT"},
    {"code": "SOL", "name": "索拉纳", "type": "crypto", "symbol": "SOL/USDT"},
    {"code": "BNB", "name": "币安币", "type": "crypto", "symbol": "BNB/USDT"},
    
    # --- 全球指数 ---
    {"code": "NDX", "name": "纳斯达克100", "type": "index", "symbol": "^NDX"},
    {"code": "SPX", "name": "标普500", "type": "index", "symbol": "^GSPC"},
    {"code": "DJI", "name": "道琼斯", "type": "index", "symbol": "^DJI"},
    {"code": "HSI", "name": "恒生指数", "type": "index", "symbol": "^HSI"},
    
    # --- 美股科技股 ---
    {"code": "NVDA", "name": "英伟达", "type": "stock_us", "symbol": "NVDA"},
    {"code": "TSLA", "name": "特斯拉", "type": "stock_us", "symbol": "TSLA"},
    {"code": "AAPL", "name": "苹果", "type": "stock_us", "symbol": "AAPL"},
    {"code": "MSFT", "name": "微软", "type": "stock_us", "symbol": "MSFT"},
    {"code": "GOOGL", "name": "谷歌", "type": "stock_us", "symbol": "GOOGL"},
    {"code": "META", "name": "Meta", "type": "stock_us", "symbol": "META"},
    {"code": "AMZN", "name": "亚马逊", "type": "stock_us", "symbol": "AMZN"},
    
    # --- 大宗商品 ---
    {"code": "GOLD", "name": "黄金", "type": "commodity", "symbol": "GC=F"},
    {"code": "SILVER", "name": "白银", "type": "commodity", "symbol": "SI=F"},
    {"code": "OIL", "name": "原油", "type": "commodity", "symbol": "CL=F"},
    
    # --- QDII基金 (通过锚定指数估算) ---
    {"code": "004046", "name": "华安纳斯达克100", "type": "fund_qdii", "benchmark": "^NDX"},
    {"code": "161125", "name": "易方达标普500", "type": "fund_qdii", "benchmark": "^GSPC"},
    
    # --- A股基金 (通过持仓穿透估算) ---
    {"code": "161725", "name": "招商中证白酒", "type": "fund_cn", 
     "holdings": ["600519", "000858", "000568", "000596", "002304"]},
    {"code": "512480", "name": "半导体ETF", "type": "fund_cn",
     "holdings": ["603501", "603986", "002371", "688012", "002156"]},
]

def get_crypto_data(symbol):
    """抓取加密货币数据 (Binance)"""
    try:
        exchange = ccxt.binance()
        ticker = exchange.fetch_ticker(symbol)
        return {
            "price": round(ticker['last'], 2),
            "change": round(ticker['percentage'], 2)
        }
    except Exception as e:
        print(f"  ✗ 加密货币 {symbol}: {str(e)[:30]}")
        return {"price": 0, "change": 0}

def get_yahoo_data(symbol):
    """抓取美股/指数/商品 (Yahoo Finance)"""
    try:
        ticker = yf.Ticker(symbol)
        
        # 尝试获取实时数据
        try:
            info = ticker.fast_info
            price = info.last_price
            prev_close = info.previous_close
            change = ((price - prev_close) / prev_close) * 100
        except:
            # 备用：历史数据
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                change = ((price - prev_close) / prev_close) * 100
            else:
                return {"price": 0, "change": 0}
        
        return {
            "price": round(price, 2),
            "change": round(change, 2)
        }
    except Exception as e:
        print(f"  ✗ Yahoo {symbol}: {str(e)[:30]}")
        return {"price": 0, "change": 0}

def get_cn_stock_change(code):
    """抓取A股涨跌幅 (AkShare)"""
    try:
        df = ak.stock_zh_a_spot_em()
        stock = df[df['代码'] == code]
        if not stock.empty:
            return float(stock['涨跌幅'].values[0])
        return 0.0
    except:
        return 0.0

def process_asset(item):
    """处理单个资产"""
    print(f"[{item['code']}] {item['name']}...", end=" ")
    
    res = {
        "code": item["code"],
        "name": item["name"],
        "market": item["type"],
        "price": 0,
        "change_pct": 0,
        "success": False
    }
    
    try:
        if item["type"] == "crypto":
            data = get_crypto_data(item["symbol"])
            res["price"] = data["price"]
            res["change_pct"] = data["change"]
            res["success"] = data["price"] > 0
            
        elif item["type"] in ["index", "commodity", "stock_us"]:
            data = get_yahoo_data(item["symbol"])
            res["price"] = data["price"]
            res["change_pct"] = data["change"]
            res["success"] = data["price"] > 0
            
        elif item["type"] == "fund_cn":
            # A股基金：持仓穿透估算
            total_change = 0
            count = 0
            for stock in item["holdings"]:
                chg = get_cn_stock_change(stock)
                if chg != 0:
                    total_change += chg
                    count += 1
            if count > 0:
                res["change_pct"] = round(total_change / count, 2)
                res["success"] = True
                
        elif item["type"] == "fund_qdii":
            # QDII基金：锚定指数估算
            data = get_yahoo_data(item["benchmark"])
            res["change_pct"] = data["change"]
            res["success"] = data["change"] != 0
        
        if res["success"]:
            print(f"{res['change_pct']:+.2f}% ✓")
        else:
            print("✗")
            
    except Exception as e:
        print(f"✗ {str(e)[:30]}")
    
    return res

def main():
    print("=" * 60)
    print(f"开始抓取 {len(ASSETS)} 个全球资产数据")
    print("=" * 60)
    
    os.makedirs("data", exist_ok=True)
    
    results = []
    success_count = 0
    
    # 并发抓取（提高速度）
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_asset, asset) for asset in ASSETS]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            if result["success"]:
                success_count += 1
    
    # 按类型分组
    grouped = {
        "crypto": [],
        "index": [],
        "stock_us": [],
        "commodity": [],
        "fund_qdii": [],
        "fund_cn": []
    }
    
    for r in results:
        if r["market"] in grouped:
            grouped[r["market"]].append(r)
    
    # 保存结果
    tz = pytz.timezone('Asia/Shanghai')
    output = {
        "last_updated": datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S'),
        "total_count": len(results),
        "success_count": success_count,
        "assets": results,
        "grouped": grouped
    }
    
    with open("data/global_assets.json", "w", encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("=" * 60)
    print(f"完成！成功: {success_count}/{len(results)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
