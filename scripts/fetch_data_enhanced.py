import akshare as ak
import pandas as pd
import json
import os
from datetime import datetime
import pytz
import time
import requests

# 股票名称缓存
STOCK_NAME_CACHE = {}

def get_stock_info(stock_code):
    """获取股票完整信息（名称、实时价格、涨跌幅）"""
    # 先检查缓存
    if stock_code in STOCK_NAME_CACHE:
        return STOCK_NAME_CACHE[stock_code]
    
    try:
        # 方法1：从实时行情获取
        df = ak.stock_zh_a_spot_em()
        stock = df[df['代码'] == stock_code]
        if not stock.empty:
            info = {
                '名称': str(stock['名称'].values[0]),
                '最新价': float(stock['最新价'].values[0]),
                '涨跌幅': float(stock['涨跌幅'].values[0])
            }
            STOCK_NAME_CACHE[stock_code] = info
            return info
    except Exception as e:
        print(f"    获取股票 {stock_code} 信息失败: {str(e)[:30]}")
    
    # 方法2：从个股信息获取
    try:
        info_df = ak.stock_individual_info_em(symbol=stock_code)
        name = info_df.loc[info_df['item'] == '股票简称', 'value'].values[0]
        info = {
            '名称': str(name),
            '最新价': 0.0,
            '涨跌幅': 0.0
        }
        STOCK_NAME_CACHE[stock_code] = info
        return info
    except:
        pass
    
    return None

def get_accurate_valuation(code):
    """获取最准确的估值数据"""
    try:
        # 天天基金实时估值接口（最准确）
        url = f"http://fundgz.1234567.com.cn/js/{code}.js"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data_str = response.text
            data_str = data_str.replace('jsonpgz(', '').replace(');', '')
            data = json.loads(data_str)
            
            return {
                'estimation': float(data['gszzl']),
                'net_value': float(data['dwjz']),
                'est_value': float(data['gsz']),
                'update_time': data['gztime'],
                'source': '天天基金实时'
            }
    except:
        pass
    
    # 备用方法：akshare
    try:
        gz_data = ak.fund_em_value_estimation_em(symbol=code)
        if not gz_data.empty:
            return {
                'estimation': float(gz_data['估值涨跌幅'].iloc[0]),
                'net_value': float(gz_data['单位净值'].iloc[0]) if '单位净值' in gz_data.columns else 0,
                'est_value': float(gz_data['估算净值'].iloc[0]) if '估算净值' in gz_data.columns else 0,
                'update_time': str(gz_data['最新更新时间'].iloc[0]),
                'source': 'akshare'
            }
    except:
        pass
    
    return None

def get_fund_valuation(code, name):
    """获取基金完整信息（包含真实股票名称）"""
    print(f"[{code}] {name}...", end=" ")
    
    try:
        # 获取估值
        valuation = get_accurate_valuation(code)
        if valuation:
            estimation = valuation['estimation']
            net_value = valuation['net_value']
            est_value = valuation['est_value']
            est_time = valuation['update_time']
            data_source = valuation['source']
            print(f"{estimation:+.2f}%", end=" ")
        else:
            estimation = 0.0
            net_value = 0.0
            est_value = 0.0
            est_time = "无数据"
            data_source = "无"
            print("无估值", end=" ")

        # 获取持仓（增强版：获取真实股票名称）
        holdings = []
        try:
            portfolio = ak.fund_portfolio_hold_em(symbol=code, date="")
            if not portfolio.empty:
                stock_holdings = portfolio[portfolio['资产类别'] == '股票']
                if not stock_holdings.empty:
                    print(f"持仓{len(stock_holdings)}只", end="")
                    
                    for idx, row in stock_holdings.head(10).iterrows():
                        stock_code = str(row['股票代码'])
                        stock_name = str(row['股票名称'])
                        holding_ratio = float(row['占净值比例'])
                        
                        # 如果股票名称是占位符或为空，获取真实名称
                        if (stock_name.startswith('股票') or 
                            stock_name == '' or 
                            len(stock_name) < 2 or
                            stock_name == 'nan'):
                            
                            stock_info = get_stock_info(stock_code)
                            if stock_info:
                                stock_name = stock_info['名称']
                                print(".", end="")
                            else:
                                stock_name = f"未知({stock_code})"
                        
                        holdings.append({
                            "股票名称": stock_name,
                            "持仓比例": holding_ratio,
                            "股票代码": stock_code,
                        })
                    
                    print(f" ✓{len(holdings)}股")
                else:
                    print("✗无股票持仓")
        except Exception as e:
            print(f"✗持仓获取失败")

        return {
            "code": code,
            "name": name,
            "estimation": round(estimation, 2),
            "net_value": round(net_value, 4) if net_value > 0 else None,
            "est_value": round(est_value, 4) if est_value > 0 else None,
            "update_time": est_time,
            "data_source": data_source,
            "holdings": holdings,
            "success": True
        }

    except Exception as e:
        print(f"✗ {str(e)[:30]}")
        return {
            "code": code,
            "name": name,
            "success": False,
            "error": str(e)
        }

# 导入基金列表（从 fetch_data.py）
from fetch_data import WATCH_LIST

def main():
    print("=" * 60)
    print(f"开始抓取 {len(WATCH_LIST)} 只基金的准确估值数据（增强版）")
    print("包含真实股票名称")
    print("=" * 60)
    
    os.makedirs("data", exist_ok=True)
    os.makedirs("public/data", exist_ok=True)

    results = []
    success_count = 0
    
    for i, (code, name) in enumerate(WATCH_LIST.items(), 1):
        print(f"[{i}/{len(WATCH_LIST)}] ", end="")
        data = get_fund_valuation(code, name)
        results.append(data)
        
        if data['success']:
            success_count += 1
        
        # 添加延迟避免请求过快
        if i < len(WATCH_LIST):
            time.sleep(0.3)

    beijing_tz = pytz.timezone('Asia/Shanghai')
    last_updated = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')

    final_output = {
        "last_updated": last_updated,
        "total_count": len(results),
        "success_count": success_count,
        "funds": results
    }

    # 保存到两个位置
    with open("data/funds.json", "w", encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    
    with open("public/data/funds.json", "w", encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print(f"完成！成功: {success_count}/{len(results)}")
    print(f"股票名称缓存: {len(STOCK_NAME_CACHE)} 只")
    print("=" * 60)

if __name__ == "__main__":
    main()
