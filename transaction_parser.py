#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import re


class TransactionAnalyzer:
    """Lightweight transaction parser (no GUI dependencies)."""

    @staticmethod
    def parse_transaction_file(file_path_or_buffer):
        try:
            df = pd.read_excel(file_path_or_buffer)
            required_columns = ['تاریخ', 'شرح', 'بدهکار', 'بستانکار', 'مانده']
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"Column '{col}' not found in the transaction file")
            return df
        except Exception as e:
            raise Exception(f"Error parsing transaction file: {str(e)}")

    @staticmethod
    def extract_option_transactions(df):
        option_transactions = []

        buy_pattern = re.compile(r'خرید\s+(\d+)\s+سهم\s+(ض|ط)هرم(\d+)\s+به\s+نرخ\s+(\d+)')
        sell_pattern = re.compile(r'فروش\s+(\d+)\s+سهم\s+(ض|ط)هرم(\d+)\s+به\s+نرخ\s+(\d+)')

        for index, row in df.iterrows():
            description = str(row['شرح'])
            date = row['تاریخ']
            debit = row.get('بدهکار', None)
            credit = row.get('بستانکار', None)

            buy_match = buy_pattern.search(description)
            if buy_match:
                quantity = int(buy_match.group(1))
                option_type = 'Call' if buy_match.group(2) == 'ض' else 'Put'
                strike_code = buy_match.group(3)
                price = float(buy_match.group(4))

                transaction = {
                    'date': date,
                    'action': 'Buy',
                    'symbol': f"{buy_match.group(2)}هرم{strike_code}",
                    'option_type': option_type,
                    'strike_code': strike_code,
                    'quantity': quantity,
                    'price': price,
                    'amount': debit
                }
                option_transactions.append(transaction)
                continue

            sell_match = sell_pattern.search(description)
            if sell_match:
                quantity = int(sell_match.group(1))
                option_type = 'Call' if sell_match.group(2) == 'ض' else 'Put'
                strike_code = sell_match.group(3)
                price = float(sell_match.group(4))

                transaction = {
                    'date': date,
                    'action': 'Sell',
                    'symbol': f"{sell_match.group(2)}هرم{strike_code}",
                    'option_type': option_type,
                    'strike_code': strike_code,
                    'quantity': quantity,
                    'price': price,
                    'amount': credit
                }
                option_transactions.append(transaction)

        return option_transactions

    @staticmethod
    def calculate_positions(transactions):
        positions = {}
        for transaction in transactions:
            symbol = transaction['symbol']
            quantity = transaction['quantity']
            action = transaction['action']

            if symbol not in positions:
                positions[symbol] = {
                    'symbol': symbol,
                    'option_type': transaction['option_type'],
                    'strike_code': transaction['strike_code'],
                    'quantity': 0,
                    'avg_price': 0,
                    'total_cost': 0
                }

            position = positions[symbol]
            if action == 'Buy':
                current_quantity = position['quantity']
                current_cost = position['total_cost']
                new_quantity = current_quantity + quantity
                new_cost = current_cost + (quantity * transaction['price'])
                position['quantity'] = new_quantity
                position['total_cost'] = new_cost
                position['avg_price'] = new_cost / new_quantity if new_quantity > 0 else 0
            elif action == 'Sell':
                position['quantity'] -= quantity

        open_positions = {k: v for k, v in positions.items() if v['quantity'] != 0}
        position_list = []
        strike_mapping = {
            '0119': 24000,
            '0120': 26000,
            '0121': 28000,
            '0122': 30000,
            '2018': 18000
        }

        for symbol, position in open_positions.items():
            position_type = 'Long' if position['quantity'] > 0 else 'Short'
            strike_price = strike_mapping.get(position['strike_code'], 25000)
            position_entry = {
                'type': position['option_type'],
                'position': position_type,
                'strike': strike_price,
                'quantity': abs(position['quantity']),
                'premium': position['avg_price'],
                'symbol': position['symbol']
            }
            position_list.append(position_entry)

        return position_list
