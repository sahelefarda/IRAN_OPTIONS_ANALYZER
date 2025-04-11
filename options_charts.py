import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for compatibility
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

class OptionsChartGenerator:
    """Class for generating option strategy charts"""
    
    @staticmethod
    def generate_pnl_chart(price_range, pnl_values, current_price, title="Strategy Profit/Loss"):
        """Generate profit/loss chart for an options strategy"""
        plt.figure(figsize=(10, 6))
        plt.plot(price_range, pnl_values, 'b-', linewidth=2)
        plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        plt.axvline(x=current_price, color='r', linestyle='--', alpha=0.5, label='Current Price')
        
        # Add breakeven points
        breakeven_indices = np.where(np.diff(np.signbit(pnl_values)))[0]
        for idx in breakeven_indices:
            # Linear interpolation to find more accurate breakeven point
            x1, x2 = price_range[idx], price_range[idx+1]
            y1, y2 = pnl_values[idx], pnl_values[idx+1]
            breakeven = x1 + (x2 - x1) * (0 - y1) / (y2 - y1)
            plt.plot(breakeven, 0, 'go', markersize=8)
            plt.annotate(f'{breakeven:.2f}', (breakeven, 0), 
                         textcoords="offset points", xytext=(0,10), 
                         ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.3))
        
        # Add max profit/loss points
        max_profit_idx = np.argmax(pnl_values)
        max_loss_idx = np.argmin(pnl_values)
        
        plt.plot(price_range[max_profit_idx], pnl_values[max_profit_idx], 'go', markersize=8)
        plt.annotate(f'Max Profit: {pnl_values[max_profit_idx]:.2f}', 
                     (price_range[max_profit_idx], pnl_values[max_profit_idx]), 
                     textcoords="offset points", xytext=(0,10), 
                     ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="lightgreen", alpha=0.3))
        
        plt.plot(price_range[max_loss_idx], pnl_values[max_loss_idx], 'ro', markersize=8)
        plt.annotate(f'Max Loss: {pnl_values[max_loss_idx]:.2f}', 
                     (price_range[max_loss_idx], pnl_values[max_loss_idx]), 
                     textcoords="offset points", xytext=(0,-20), 
                     ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="lightcoral", alpha=0.3))
        
        plt.title(title, fontsize=14, fontweight='bold')
        plt.xlabel('Underlying Price', fontsize=12)
        plt.ylabel('Profit/Loss', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        return plt.gcf()
    
    @staticmethod
    def generate_greek_chart(price_range, greek_values, current_price, greek_name, color='g'):
        """Generate chart for a specific Greek"""
        plt.figure(figsize=(10, 6))
        plt.plot(price_range, greek_values, f'{color}-', linewidth=2)
        plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        plt.axvline(x=current_price, color='r', linestyle='--', alpha=0.5, label='Current Price')
        
        # Add current value
        current_idx = np.abs(price_range - current_price).argmin()
        current_value = greek_values[current_idx]
        
        plt.plot(current_price, current_value, 'bo', markersize=8)
        plt.annotate(f'Current {greek_name}: {current_value:.4f}', 
                     (current_price, current_value), 
                     textcoords="offset points", xytext=(0,10), 
                     ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="lightskyblue", alpha=0.3))
        
        # Add extrema points
        max_idx = np.argmax(greek_values)
        min_idx = np.argmin(greek_values)
        
        if max_idx != current_idx:
            plt.plot(price_range[max_idx], greek_values[max_idx], 'go', markersize=8)
            plt.annotate(f'Max: {greek_values[max_idx]:.4f}', 
                        (price_range[max_idx], greek_values[max_idx]), 
                        textcoords="offset points", xytext=(0,10), 
                        ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="lightgreen", alpha=0.3))
        
        if min_idx != current_idx and min_idx != max_idx:
            plt.plot(price_range[min_idx], greek_values[min_idx], 'ro', markersize=8)
            plt.annotate(f'Min: {greek_values[min_idx]:.4f}', 
                        (price_range[min_idx], greek_values[min_idx]), 
                        textcoords="offset points", xytext=(0,-20), 
                        ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="lightcoral", alpha=0.3))
        
        plt.title(f'Strategy {greek_name}', fontsize=14, fontweight='bold')
        plt.xlabel('Underlying Price', fontsize=12)
        plt.ylabel(greek_name, fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        return plt.gcf()
    
    @staticmethod
    def generate_gamma_surface_chart(strike_prices, days_range, gamma_values):
        """Generate 3D surface chart for gamma across strikes and time"""
        from mpl_toolkits.mplot3d import Axes3D
        
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        X, Y = np.meshgrid(strike_prices, days_range)
        
        # Plot the surface
        surf = ax.plot_surface(X, Y, gamma_values, cmap='viridis', alpha=0.8, 
                              linewidth=0, antialiased=True)
        
        # Add color bar
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='Gamma')
        
        ax.set_title('Gamma Surface', fontsize=14, fontweight='bold')
        ax.set_xlabel('Strike Price', fontsize=12)
        ax.set_ylabel('Days to Expiry', fontsize=12)
        ax.set_zlabel('Gamma', fontsize=12)
        
        return fig
    
    @staticmethod
    def generate_gamma_vs_strike_chart(strike_prices, gamma_values, current_price):
        """Generate chart for gamma vs strike price"""
        plt.figure(figsize=(10, 6))
        plt.plot(strike_prices, gamma_values, 'r-', linewidth=2)
        plt.axvline(x=current_price, color='b', linestyle='--', alpha=0.5, label='Current Price')
        
        # Add current value
        current_idx = np.abs(strike_prices - current_price).argmin()
        current_value = gamma_values[current_idx]
        
        plt.plot(current_price, current_value, 'bo', markersize=8)
        plt.annotate(f'Current Gamma: {current_value:.6f}', 
                     (current_price, current_value), 
                     textcoords="offset points", xytext=(0,10), 
                     ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="lightskyblue", alpha=0.3))
        
        # Add max gamma point
        max_idx = np.argmax(gamma_values)
        
        plt.plot(strike_prices[max_idx], gamma_values[max_idx], 'go', markersize=8)
        plt.annotate(f'Max Gamma: {gamma_values[max_idx]:.6f}', 
                    (strike_prices[max_idx], gamma_values[max_idx]), 
                    textcoords="offset points", xytext=(0,10), 
                    ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="lightgreen", alpha=0.3))
        
        plt.title('Gamma vs Strike Price', fontsize=14, fontweight='bold')
        plt.xlabel('Strike Price', fontsize=12)
        plt.ylabel('Gamma', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        return plt.gcf()
    
    @staticmethod
    def generate_gamma_vs_time_chart(days_range, gamma_values, current_days):
        """Generate chart for gamma vs time to expiry"""
        plt.figure(figsize=(10, 6))
        plt.plot(days_range, gamma_values, 'r-', linewidth=2)
        plt.axvline(x=current_days, color='b', linestyle='--', alpha=0.5, label='Current Days')
        
        # Add current value
        current_idx = np.abs(days_range - current_days).argmin()
        current_value = gamma_values[current_idx]
        
        plt.plot(current_days, current_value, 'bo', markersize=8)
        plt.annotate(f'Current Gamma: {current_value:.6f}', 
                     (current_days, current_value), 
                     textcoords="offset points", xytext=(0,10), 
                     ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="lightskyblue", alpha=0.3))
        
        plt.title('Gamma vs Days to Expiry', fontsize=14, fontweight='bold')
        plt.xlabel('Days to Expiry', fontsize=12)
        plt.ylabel('Gamma', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        return plt.gcf()
    
    @staticmethod
    def generate_gamma_to_theta_ratio_chart(price_range, gamma_values, theta_values, current_price):
        """Generate chart for gamma/theta ratio"""
        # Avoid division by zero
        epsilon = 1e-10
        ratio = np.array(gamma_values) / (np.abs(np.array(theta_values)) + epsilon)
        
        plt.figure(figsize=(10, 6))
        plt.plot(price_range, ratio, 'purple', linewidth=2)
        plt.axvline(x=current_price, color='r', linestyle='--', alpha=0.5, label='Current Price')
        
        # Add current value
        current_idx = np.abs(price_range - current_price).argmin()
        current_value = ratio[current_idx]
        
        plt.plot(current_price, current_value, 'bo', markersize=8)
        plt.annotate(f'Current Ratio: {current_value:.4f}', 
                     (current_price, current_value), 
                     textcoords="offset points", xytext=(0,10), 
                     ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="lightskyblue", alpha=0.3))
        
        # Add max ratio point
        max_idx = np.argmax(ratio)
        
        plt.plot(price_range[max_idx], ratio[max_idx], 'go', markersize=8)
        plt.annotate(f'Max Ratio: {ratio[max_idx]:.4f}', 
                    (price_range[max_idx], ratio[max_idx]), 
                    textcoords="offset points", xytext=(0,10), 
                    ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="lightgreen", alpha=0.3))
        
        plt.title('Gamma/Theta Ratio (Higher is better for scalping)', fontsize=14, fontweight='bold')
        plt.xlabel('Underlying Price', fontsize=12)
        plt.ylabel('Gamma/Theta Ratio', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        return plt.gcf()
    
    @staticmethod
    def generate_all_greeks_comparison_chart(price_range, delta, gamma, theta, vega, current_price):
        """Generate chart comparing all Greeks on the same plot (normalized)"""
        # Normalize Greeks to compare on same scale
        def normalize(data):
            return (data - np.min(data)) / (np.max(data) - np.min(data))
        
        norm_delta = normalize(delta)
        norm_gamma = normalize(gamma)
        norm_theta = normalize(np.abs(theta))  # Use absolute value for theta
        norm_vega = normalize(vega)
        
        plt.figure(figsize=(12, 7))
        plt.plot(price_range, norm_delta, 'g-', linewidth=2, label='Delta')
        plt.plot(price_range, norm_gamma, 'r-', linewidth=2, label='Gamma')
        plt.plot(price_range, norm_theta, 'c-', linewidth=2, label='Theta (abs)')
        plt.plot(price_range, norm_vega, 'm-', linewidth=2, label='Vega')
        plt.axvline(x=current_price, color='k', linestyle='--', alpha=0.5, label='Current Price')
        
        plt.title('Normalized Greeks Comparison', fontsize=14, fontweight='bold')
        plt.xlabel('Underlying Price', fontsize=12)
        plt.ylabel('Normalized Value (0-1)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        return plt.gcf()
