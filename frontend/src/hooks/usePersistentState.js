/**
 * Custom hook for persistent state management with localStorage
 */

import { useState, useEffect, useCallback } from 'react';

export function usePersistentState(key, defaultValue) {
  const [state, setState] = useState(() => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.error(`Error loading persisted state for key "${key}":`, error);
      return defaultValue;
    }
  });

  const setValue = useCallback((value) => {
    try {
      // Allow value to be a function so we have the same API as useState
      const valueToStore = value instanceof Function ? value(state) : value;
      setState(valueToStore);
      localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(`Error saving state to localStorage for key "${key}":`, error);
    }
  }, [key, state]);

  const removeValue = useCallback(() => {
    try {
      localStorage.removeItem(key);
      setState(defaultValue);
    } catch (error) {
      console.error(`Error removing state from localStorage for key "${key}":`, error);
    }
  }, [key, defaultValue]);

  return [state, setValue, removeValue];
}

export function useSessionStorage(key, defaultValue) {
  const [state, setState] = useState(() => {
    try {
      const item = sessionStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.error(`Error loading session state for key "${key}":`, error);
      return defaultValue;
    }
  });

  const setValue = useCallback((value) => {
    try {
      const valueToStore = value instanceof Function ? value(state) : value;
      setState(valueToStore);
      sessionStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(`Error saving state to sessionStorage for key "${key}":`, error);
    }
  }, [key, state]);

  const removeValue = useCallback(() => {
    try {
      sessionStorage.removeItem(key);
      setState(defaultValue);
    } catch (error) {
      console.error(`Error removing state from sessionStorage for key "${key}":`, error);
    }
  }, [key, defaultValue]);

  return [state, setValue, removeValue];
}

export default usePersistentState;
