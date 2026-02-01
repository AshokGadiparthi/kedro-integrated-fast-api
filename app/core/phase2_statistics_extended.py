"""
Phase 2: Advanced Statistics with Visualizations
Extends UniversalEDAAnalyzer with:
- Histogram data (binning)
- Outlier detection
- Normality tests (Shapiro-Wilk)
- Distribution analysis
"""

import pandas as pd
import numpy as np
from scipy import stats
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


class Phase2StatisticsExtended:
    """
    Extended statistics for Phase 2 - Visualization ready!
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    # =========================================================================
    # HISTOGRAMS - For Visualization
    # =========================================================================
    
    def get_histograms(self, bins: int = 10) -> Dict[str, Any]:
        """
        Generate histogram data for numeric columns
        Returns data ready for Plotly/Recharts visualization
        """
        histograms = {}
        
        for col in self.numeric_cols:
            col_data = self.df[col].dropna()
            
            if len(col_data) == 0:
                continue
            
            try:
                # Create histogram data
                counts, bin_edges = np.histogram(col_data, bins=bins)
                
                # Create bin labels
                bin_labels = []
                for i in range(len(bin_edges) - 1):
                    start = round(bin_edges[i], 2)
                    end = round(bin_edges[i + 1], 2)
                    bin_labels.append(f"{start}-{end}")
                
                histograms[col] = {
                    "column": col,
                    "bins": bin_labels,
                    "frequencies": [int(c) for c in counts],
                    "bin_edges": [float(e) for e in bin_edges],
                    "total_count": int(len(col_data)),
                    "missing_count": int(col_data.isna().sum()),
                    "statistics": {
                        "mean": float(col_data.mean()),
                        "median": float(col_data.median()),
                        "std": float(col_data.std()),
                        "min": float(col_data.min()),
                        "max": float(col_data.max()),
                        "q1": float(col_data.quantile(0.25)),
                        "q3": float(col_data.quantile(0.75))
                    }
                }
            except Exception as e:
                logger.warning(f"Failed to generate histogram for {col}: {str(e)}")
                continue
        
        return {
            "dataset_id": None,  # Will be set by endpoint
            "histograms": histograms,
            "total_numeric_columns": len(self.numeric_cols),
            "successfully_generated": len(histograms)
        }
    
    # =========================================================================
    # OUTLIERS - IQR Method
    # =========================================================================
    
    def get_outliers(self) -> Dict[str, Any]:
        """
        Detect outliers using IQR method (Interquartile Range)
        """
        outliers_data = {}
        
        for col in self.numeric_cols:
            col_data = self.df[col].dropna()
            
            if len(col_data) < 4:  # Need at least 4 values for IQR
                continue
            
            try:
                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1
                
                # Define outlier bounds
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Find outliers
                outlier_mask = (col_data < lower_bound) | (col_data > upper_bound)
                outlier_values = col_data[outlier_mask]
                
                outliers_data[col] = {
                    "column": col,
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound),
                    "IQR": float(IQR),
                    "outlier_count": int(len(outlier_values)),
                    "outlier_percentage": round(len(outlier_values) / len(col_data) * 100, 2),
                    "outlier_indices": [int(i) for i in col_data[outlier_mask].index.tolist()[:100]],  # First 100
                    "min_outlier": float(outlier_values.min()) if len(outlier_values) > 0 else None,
                    "max_outlier": float(outlier_values.max()) if len(outlier_values) > 0 else None,
                    "statistics": {
                        "mean": float(col_data.mean()),
                        "median": float(col_data.median()),
                        "q1": float(Q1),
                        "q3": float(Q3)
                    }
                }
            except Exception as e:
                logger.warning(f"Failed to detect outliers for {col}: {str(e)}")
                continue
        
        return {
            "dataset_id": None,
            "outliers": outliers_data,
            "total_numeric_columns": len(self.numeric_cols),
            "columns_with_outliers": len([c for c in outliers_data if outliers_data[c]["outlier_count"] > 0]),
            "method": "IQR (Interquartile Range)"
        }
    
    # =========================================================================
    # NORMALITY TESTS - Shapiro-Wilk Test
    # =========================================================================
    
    def get_normality_tests(self) -> Dict[str, Any]:
        """
        Test normality using Shapiro-Wilk test
        p-value > 0.05 means data is approximately normal
        """
        normality_tests = {}
        
        for col in self.numeric_cols:
            col_data = self.df[col].dropna()
            
            # Shapiro-Wilk test works best with 3-5000 samples
            if len(col_data) < 3 or len(col_data) > 5000:
                # For very large or very small samples, use a sample
                if len(col_data) > 5000:
                    col_data = col_data.sample(n=5000, random_state=42)
                elif len(col_data) < 3:
                    continue
            
            try:
                # Shapiro-Wilk test
                stat, p_value = stats.shapiro(col_data)
                
                # Interpretation
                is_normal = p_value > 0.05
                
                # Calculate skewness and kurtosis
                skewness = float(col_data.skew())
                kurtosis = float(col_data.kurtosis())
                
                normality_tests[col] = {
                    "column": col,
                    "test": "Shapiro-Wilk",
                    "statistic": float(stat),
                    "p_value": float(p_value),
                    "is_normal": bool(is_normal),
                    "interpretation": "Approximately normal" if is_normal else "Not normally distributed",
                    "skewness": skewness,
                    "kurtosis": kurtosis,
                    "sample_size": int(len(col_data))
                }
            except Exception as e:
                logger.warning(f"Failed normality test for {col}: {str(e)}")
                continue
        
        return {
            "dataset_id": None,
            "normality_tests": normality_tests,
            "total_numeric_columns": len(self.numeric_cols),
            "normal_columns": len([c for c in normality_tests if normality_tests[c]["is_normal"]]),
            "non_normal_columns": len([c for c in normality_tests if not normality_tests[c]["is_normal"]])
        }
    
    # =========================================================================
    # DISTRIBUTION TYPES - Detect Distribution Shape
    # =========================================================================
    
    def get_distribution_analysis(self) -> Dict[str, Any]:
        """
        Analyze distribution characteristics
        """
        distributions = {}
        
        for col in self.numeric_cols:
            col_data = self.df[col].dropna()
            
            if len(col_data) < 10:
                continue
            
            try:
                skewness = col_data.skew()
                kurt = col_data.kurtosis()
                
                # Determine distribution type
                if abs(skewness) < 0.5:
                    dist_type = "Approximately Symmetric"
                elif skewness > 0.5:
                    dist_type = "Right-skewed (Positive skew)"
                else:
                    dist_type = "Left-skewed (Negative skew)"
                
                # Kurtosis interpretation
                if abs(kurt) < 0.5:
                    kurtosis_type = "Mesokurtic (normal-like)"
                elif kurt > 0.5:
                    kurtosis_type = "Leptokurtic (heavy tails)"
                else:
                    kurtosis_type = "Platykurtic (light tails)"
                
                distributions[col] = {
                    "column": col,
                    "skewness": float(skewness),
                    "kurtosis": float(kurt),
                    "distribution_type": dist_type,
                    "kurtosis_type": kurtosis_type,
                    "characteristics": [
                        f"Skewness: {dist_type}",
                        f"Kurtosis: {kurtosis_type}",
                        f"Range: {float(col_data.max() - col_data.min()):.2f}",
                        f"CV: {float(col_data.std() / col_data.mean() * 100):.2f}%"
                    ]
                }
            except Exception as e:
                logger.warning(f"Failed distribution analysis for {col}: {str(e)}")
                continue
        
        return {
            "dataset_id": None,
            "distributions": distributions,
            "total_numeric_columns": len(self.numeric_cols),
            "analyzed_columns": len(distributions)
        }
    
    # =========================================================================
    # CATEGORICAL DISTRIBUTIONS
    # =========================================================================
    
    def get_categorical_distributions(self, top_n: int = 10) -> Dict[str, Any]:
        """
        Get distribution of categorical columns
        """
        categorical_dists = {}
        
        for col in self.categorical_cols:
            value_counts = self.df[col].value_counts()
            
            categorical_dists[col] = {
                "column": col,
                "unique_values": int(self.df[col].nunique()),
                "top_values": {},
                "total_rows": int(len(self.df)),
                "missing_count": int(self.df[col].isna().sum())
            }
            
            # Get top N values
            for value, count in value_counts.head(top_n).items():
                percentage = round(count / len(self.df) * 100, 2)
                categorical_dists[col]["top_values"][str(value)] = {
                    "count": int(count),
                    "percentage": percentage
                }
        
        return {
            "dataset_id": None,
            "categorical_distributions": categorical_dists,
            "total_categorical_columns": len(self.categorical_cols),
            "analyzed_columns": len(categorical_dists)
        }
    
    # =========================================================================
    # CORRELATION ANALYSIS (Enhanced)
    # =========================================================================
    
    def get_enhanced_correlations(self, threshold: float = 0.3) -> Dict[str, Any]:
        """
        Enhanced correlation analysis with p-values
        """
        if len(self.numeric_cols) < 2:
            return {
                "dataset_id": None,
                "correlations": {},
                "high_correlations": [],
                "message": "Need at least 2 numeric columns"
            }
        
        numeric_df = self.df[self.numeric_cols]
        correlations = {}
        high_correlations = []
        
        try:
            # Pearson correlation
            corr_matrix = numeric_df.corr(method='pearson')
            
            # Calculate p-values using scipy
            for i, col1 in enumerate(corr_matrix.columns):
                for j, col2 in enumerate(corr_matrix.columns):
                    if i < j:  # Avoid duplicates
                        corr_val = float(corr_matrix.loc[col1, col2])
                        
                        # Calculate p-value
                        try:
                            _, p_value = stats.pearsonr(
                                numeric_df[col1].dropna(),
                                numeric_df[col2].dropna()
                            )
                        except:
                            p_value = np.nan
                        
                        key = f"{col1}-{col2}"
                        correlations[key] = {
                            "correlation": round(corr_val, 4),
                            "p_value": round(p_value, 4) if not np.isnan(p_value) else None,
                            "significant": p_value < 0.05 if not np.isnan(p_value) else False,
                            "strength": self._correlation_strength(corr_val)
                        }
                        
                        # Collect high correlations
                        if abs(corr_val) > threshold:
                            high_correlations.append({
                                "column1": col1,
                                "column2": col2,
                                "correlation": round(corr_val, 4),
                                "p_value": round(p_value, 4) if not np.isnan(p_value) else None,
                                "strength": self._correlation_strength(corr_val)
                            })
        except Exception as e:
            logger.warning(f"Failed enhanced correlation analysis: {str(e)}")
        
        return {
            "dataset_id": None,
            "all_correlations": correlations,
            "high_correlations": sorted(high_correlations, 
                                       key=lambda x: abs(x['correlation']), 
                                       reverse=True),
            "threshold": threshold,
            "total_correlations": len(correlations),
            "high_correlation_count": len(high_correlations)
        }
    
    @staticmethod
    def _correlation_strength(corr_val: float) -> str:
        """Determine correlation strength"""
        abs_corr = abs(corr_val)
        if abs_corr >= 0.8:
            return "Very Strong"
        elif abs_corr >= 0.6:
            return "Strong"
        elif abs_corr >= 0.4:
            return "Moderate"
        elif abs_corr >= 0.2:
            return "Weak"
        else:
            return "Very Weak"


# Example usage
if __name__ == "__main__":
    df = pd.read_csv('/mnt/user-data/uploads/ecommerce_orders_dataset.csv')
    
    phase2 = Phase2StatisticsExtended(df)
    
    print("=" * 80)
    print("PHASE 2: EXTENDED STATISTICS")
    print("=" * 80)
    
    # Histograms
    print("\n📊 HISTOGRAMS")
    histograms = phase2.get_histograms(bins=15)
    print(f"Generated {histograms['successfully_generated']} histograms")
    
    # Outliers
    print("\n🔍 OUTLIERS")
    outliers = phase2.get_outliers()
    for col, data in list(outliers['outliers'].items())[:3]:
        print(f"{col}: {data['outlier_count']} outliers ({data['outlier_percentage']}%)")
    
    # Normality
    print("\n📈 NORMALITY TESTS")
    normality = phase2.get_normality_tests()
    print(f"Normal columns: {normality['normal_columns']}")
    print(f"Non-normal columns: {normality['non_normal_columns']}")
    
    # Distributions
    print("\n🎯 DISTRIBUTION ANALYSIS")
    distributions = phase2.get_distribution_analysis()
    print(f"Analyzed {distributions['analyzed_columns']} distributions")
    
    # Categorical
    print("\n📋 CATEGORICAL DISTRIBUTIONS")
    categorical = phase2.get_categorical_distributions()
    print(f"Analyzed {categorical['analyzed_columns']} categorical columns")
    
    # Enhanced correlations
    print("\n🔗 ENHANCED CORRELATIONS")
    corr = phase2.get_enhanced_correlations()
    print(f"Found {corr['high_correlation_count']} high correlations")
