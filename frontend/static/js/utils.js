/**
 * TDOA Frontend Utilities
 * Reusable functions untuk frontend
 */

// ==================== STRING UTILITIES ====================

const StringUtils = {
    /**
     * Format bytes ke readable format
     */
    formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
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
        return str.length > maxLength ? str.substring(0, maxLength) + '...' : str;
    },
    
    /**
     * Capitalize first letter
     */
    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
};

// ==================== DATE UTILITIES ====================

const DateUtils = {
    /**
     * Format date ke readable format
     */
    formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
        if (typeof date === 'string') {
            date = new Date(date);
        }
        
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
        if (typeof date === 'string') {
            date = new Date(date);
        }
        
        const seconds = Math.floor((new Date() - date) / 1000);
        
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
    }
};

// ==================== NUMBER UTILITIES ====================

const NumberUtils = {
    /**
     * Format number dengan thousands separator
     */
    formatNumber(num, decimals = 0) {
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
        return (value - min) / (max - min);
    },
    
    /**
     * Denormalize value
     */
    denormalize(value, min, max) {
        return value * (max - min) + min;
    }
};

// ==================== VALIDATION ====================

const Validators = {
    /**
     * Validate email
     */
    isEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    },
    
    /**
     * Validate URL
     */
    isURL(url) {
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
    }
};

// ==================== ARRAY UTILITIES ====================

const ArrayUtils = {
    /**
     * Check if array contains value
     */
    contains(arr, value) {
        return arr.includes(value);
    },
    
    /**
     * Get unique values dari array
     */
    unique(arr) {
        return [...new Set(arr)];
    },
    
    /**
     * Flatten nested array
     */
    flatten(arr) {
        return arr.reduce((flat, toFlatten) => {
            return flat.concat(Array.isArray(toFlatten) ? this.flatten(toFlatten) : toFlatten);
        }, []);
    },
    
    /**
     * Shuffle array
     */
    shuffle(arr) {
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
        return arr.reduce((groups, item) => {
            const value = item[key];
            if (!groups[value]) groups[value] = [];
            groups[value].push(item);
            return groups;
        }, {});
    }
};

// ==================== STORAGE UTILITIES ====================

const StorageUtils = {
    /**
     * Save ke localStorage
     */
    setLocal(key, value) {
        try {
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
    }
};

// ==================== DEBOUNCE & THROTTLE ====================

/**
 * Debounce function
 */
function debounce(func, wait = 300) {
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
 * Throttle function
 */
function throttle(func, limit = 300) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ==================== EXPORT ====================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        StringUtils,
        DateUtils,
        NumberUtils,
        Validators,
        ArrayUtils,
        StorageUtils,
        debounce,
        throttle
    };
}