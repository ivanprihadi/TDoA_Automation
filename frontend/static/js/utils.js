/**
 * TDOA Frontend Utilities Library
 * Reusable functions for common tasks
 */

// ==================== STRING UTILITIES ====================

const StringUtils = {
    /**
     * Format bytes ke readable format (KB, MB, GB)
     */
    formatBytes(bytes, decimals = 2) {
        if (!bytes || bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    },

    /**
     * Format duration dalam seconds ke readable format
     */
    formatDuration(seconds) {
        if (!seconds || seconds < 0) return '0s';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    },

    /**
     * Truncate string dengan ellipsis
     */
    truncate(str, maxLength = 50) {
        if (!str) return '';
        return str.length > maxLength ? str.substring(0, maxLength) + '...' : str;
    },

    /**
     * Capitalize first letter
     */
    capitalize(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    },

    /**
     * Convert to uppercase
     */
    uppercase(str) {
        return str ? str.toUpperCase() : '';
    },

    /**
     * Convert to lowercase
     */
    lowercase(str) {
        return str ? str.toLowerCase() : '';
    }
};

// ==================== DATE UTILITIES ====================

const DateUtils = {
    /**
     * Format date ke readable format
     */
    formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
        if (!date) return '';
        
        if (typeof date === 'string') {
            date = new Date(date);
        }
        
        if (isNaN(date.getTime())) return '';
        
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    },

    /**
     * Get relative time (e.g., "2 hours ago")
     */
    getRelativeTime(date) {
        if (!date) return '';
        
        if (typeof date === 'string') {
            date = new Date(date);
        }
        
        if (isNaN(date.getTime())) return '';
        
        const seconds = Math.floor((new Date() - date) / 1000);
        
        if (seconds < 60) return 'just now';
        
        let interval = seconds / 31536000;
        if (interval > 1) return Math.floor(interval) + ' years ago';
        
        interval = seconds / 2592000;
        if (interval > 1) return Math.floor(interval) + ' months ago';
        
        interval = seconds / 86400;
        if (interval > 1) return Math.floor(interval) + ' days ago';
        
        interval = seconds / 3600;
        if (interval > 1) return Math.floor(interval) + ' hours ago';
        
        interval = seconds / 60;
        if (interval > 1) return Math.floor(interval) + ' minutes ago';
        
        return 'just now';
    },

    /**
     * Get current time in HH:mm:ss format
     */
    getCurrentTime() {
        const now = new Date();
        return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
    }
};

// ==================== NUMBER UTILITIES ====================

const NumberUtils = {
    /**
     * Format number dengan thousands separator
     */
    formatNumber(num, decimals = 0) {
        if (isNaN(num)) return '0';
        return num.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    /**
     * Generate random number dalam range
     */
    randomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    },

    /**
     * Clamp value antara min dan max
     */
    clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    },

    /**
     * Normalize value (scale ke 0-1)
     */
    normalize(value, min, max) {
        if (max === min) return 0;
        return (value - min) / (max - min);
    },

    /**
     * Denormalize value
     */
    denormalize(value, min, max) {
        return value * (max - min) + min;
    },

    /**
     * Round to nearest decimal places
     */
    round(num, decimals = 2) {
        return Math.round(num * Math.pow(10, decimals)) / Math.pow(10, decimals);
    }
};

// ==================== VALIDATION ====================

const Validators = {
    /**
     * Validate email
     */
    isEmail(email) {
        if (!email) return false;
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    },

    /**
     * Validate URL
     */
    isURL(url) {
        if (!url) return false;
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    },

    /**
     * Validate latitude
     */
    isLatitude(lat) {
        return !isNaN(lat) && lat >= -90 && lat <= 90;
    },

    /**
     * Validate longitude
     */
    isLongitude(lon) {
        return !isNaN(lon) && lon >= -180 && lon <= 180;
    },

    /**
     * Validate coordinates
     */
    isCoordinates(lat, lon) {
        return this.isLatitude(lat) && this.isLongitude(lon);
    },

    /**
     * Validate frequency (FM band)
     */
    isFrequency(freq) {
        return !isNaN(freq) && freq >= 87 && freq <= 108;
    },

    /**
     * Validate positive number
     */
    isPositive(num) {
        return !isNaN(num) && num > 0;
    },

    /**
     * Validate number range
     */
    isInRange(num, min, max) {
        return !isNaN(num) && num >= min && num <= max;
    }
};

// ==================== ARRAY UTILITIES ====================

const ArrayUtils = {
    /**
     * Check if array contains value
     */
    contains(arr, value) {
        if (!arr || !Array.isArray(arr)) return false;
        return arr.includes(value);
    },

    /**
     * Get unique values dari array
     */
    unique(arr) {
        if (!arr || !Array.isArray(arr)) return [];
        return [...new Set(arr)];
    },

    /**
     * Flatten nested array
     */
    flatten(arr) {
        if (!arr || !Array.isArray(arr)) return [];
        return arr.reduce((flat, toFlatten) => {
            return flat.concat(Array.isArray(toFlatten) ? this.flatten(toFlatten) : toFlatten);
        }, []);
    },

    /**
     * Shuffle array (Fisher-Yates)
     */
    shuffle(arr) {
        if (!arr || !Array.isArray(arr)) return [];
        const shuffled = [...arr];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    },

    /**
     * Group array by key
     */
    groupBy(arr, key) {
        if (!arr || !Array.isArray(arr)) return {};
        return arr.reduce((groups, item) => {
            if (!item || typeof item !== 'object') return groups;
            const value = item[key];
            if (!groups[value]) groups[value] = [];
            groups[value].push(item);
            return groups;
        }, {});
    },

    /**
     * Find first matching item
     */
    find(arr, predicate) {
        if (!arr || !Array.isArray(arr)) return null;
        for (let item of arr) {
            if (predicate(item)) return item;
        }
        return null;
    },

    /**
     * Map array with async function
     */
    async mapAsync(arr, asyncFn) {
        if (!arr || !Array.isArray(arr)) return [];
        return Promise.all(arr.map(asyncFn));
    }
};

// ==================== STORAGE UTILITIES ====================

const StorageUtils = {
    /**
     * Save ke localStorage
     */
    setLocal(key, value) {
        try {
            if (!key) return false;
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('Storage error:', e);
            return false;
        }
    },

    /**
     * Get dari localStorage
     */
    getLocal(key, defaultValue = null) {
        try {
            if (!key) return defaultValue;
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('Storage error:', e);
            return defaultValue;
        }
    },

    /**
     * Remove dari localStorage
     */
    removeLocal(key) {
        try {
            if (!key) return false;
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('Storage error:', e);
            return false;
        }
    },

    /**
     * Clear all localStorage
     */
    clearLocal() {
        try {
            localStorage.clear();
            return true;
        } catch (e) {
            console.error('Storage error:', e);
            return false;
        }
    },

    /**
     * Check if key exists
     */
    hasLocal(key) {
        return localStorage.getItem(key) !== null;
    }
};

// ==================== DEBOUNCE & THROTTLE ====================

/**
 * Debounce function - delays execution until calls stop
 */
function debounce(func, wait = 300) {
    if (!func || typeof func !== 'function') return () => {};
    
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function - limits execution frequency
 */
function throttle(func, limit = 300) {
    if (!func || typeof func !== 'function') return () => {};
    
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Delay function - returns promise that resolves after delay
 */
function delay(ms = 1000) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ==================== EXPORT FOR MODULES ====================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        StringUtils,
        DateUtils,
        NumberUtils,
        Validators,
        ArrayUtils,
        StorageUtils,
        debounce,
        throttle,
        delay
    };
}