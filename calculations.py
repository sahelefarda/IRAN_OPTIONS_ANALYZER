#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from scipy.stats import norm


class OptionsCalculator:
    """Class for options pricing and Greeks calculations"""

    @staticmethod
    def black_scholes_price(S, K, T, r, sigma, option_type='call'):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if option_type.lower() == 'call':
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

        return price

    @staticmethod
    def calculate_delta(S, K, T, r, sigma, option_type='call'):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        if option_type.lower() == 'call':
            return norm.cdf(d1)
        else:
            return norm.cdf(d1) - 1

    @staticmethod
    def calculate_gamma(S, K, T, r, sigma):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        return norm.pdf(d1) / (S * sigma * np.sqrt(T))

    @staticmethod
    def calculate_theta(S, K, T, r, sigma, option_type='call'):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if option_type.lower() == 'call':
            theta = -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * norm.cdf(d2)
        else:
            theta = -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * norm.cdf(-d2)

        return theta / 365

    @staticmethod
    def calculate_vega(S, K, T, r, sigma):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        return S * np.sqrt(T) * norm.pdf(d1) / 100

    @staticmethod
    def calculate_rho(S, K, T, r, sigma, option_type='call'):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        if option_type.lower() == 'call':
            return K * T * np.exp(-r * T) * norm.cdf(d2) / 100
        else:
            return -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100

    @staticmethod
    def calculate_all_greeks(S, K, T, r, sigma, option_type='call'):
        price = OptionsCalculator.black_scholes_price(S, K, T, r, sigma, option_type)
        delta = OptionsCalculator.calculate_delta(S, K, T, r, sigma, option_type)
        gamma = OptionsCalculator.calculate_gamma(S, K, T, r, sigma)
        theta = OptionsCalculator.calculate_theta(S, K, T, r, sigma, option_type)
        vega = OptionsCalculator.calculate_vega(S, K, T, r, sigma)
        rho = OptionsCalculator.calculate_rho(S, K, T, r, sigma, option_type)

        return {
            'price': price,
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega,
            'rho': rho
        }


class StrategyCalculator:
    """Class for calculating strategy P&L and Greeks"""

    @staticmethod
    def calculate_strategy_metrics(positions, S_range, current_price, days_to_expiry, risk_free_rate, implied_volatility):
        T = days_to_expiry / 365.0

        strategy_pnl = np.zeros_like(S_range, dtype=float)
        strategy_delta = np.zeros_like(S_range, dtype=float)
        strategy_gamma = np.zeros_like(S_range, dtype=float)
        strategy_theta = np.zeros_like(S_range, dtype=float)
        strategy_vega = np.zeros_like(S_range, dtype=float)

        initial_prices = {}
        for i, position in enumerate(positions):
            option_type = position['type'].lower()
            strike = position['strike']
            initial_prices[i] = OptionsCalculator.black_scholes_price(
                current_price, strike, T, risk_free_rate, implied_volatility, option_type
            )

        for i, S in enumerate(S_range):
            for j, position in enumerate(positions):
                option_type = position['type'].lower()
                strike = position['strike']
                quantity = position['quantity']
                is_long = position['position'] == 'long'
                multiplier = 1 if is_long else -1

                option_price = OptionsCalculator.black_scholes_price(
                    S, strike, T, risk_free_rate, implied_volatility, option_type
                )

                position_pnl = (option_price - initial_prices[j]) * quantity * multiplier
                strategy_pnl[i] += position_pnl

                greeks = OptionsCalculator.calculate_all_greeks(
                    S, strike, T, risk_free_rate, implied_volatility, option_type
                )

                strategy_delta[i] += greeks['delta'] * quantity * multiplier
                strategy_gamma[i] += greeks['gamma'] * quantity * multiplier
                strategy_theta[i] += greeks['theta'] * quantity * multiplier
                strategy_vega[i] += greeks['vega'] * quantity * multiplier

        return {
            'price_range': S_range,
            'pnl': strategy_pnl,
            'delta': strategy_delta,
            'gamma': strategy_gamma,
            'theta': strategy_theta,
            'vega': strategy_vega
        }
