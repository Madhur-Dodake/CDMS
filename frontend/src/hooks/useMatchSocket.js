import { useState, useEffect, useRef, useCallback } from 'react';
import { matchesService } from '../services/api';

/**
 * useMatchSocket(matchId)
 * Connects to live match WebSocket stream with automatic reconnection
 * and fallback polling every 5 seconds when the socket connection is unavailable.
 */
export function useMatchSocket(matchId) {
  const [scorecard, setScorecard] = useState(null);
  const [liveData, setLiveData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const pollingTimerRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const heartbeatTimerRef = useRef(null);
  const isMountedRef = useRef(true);

  // Initial fetch and manual refresh function
  const fetchScorecard = useCallback(async (isInitial = false) => {
    if (!matchId) return;
    try {
      if (isInitial) setLoading(true);
      const data = await matchesService.getScorecard(matchId);
      if (isMountedRef.current) {
        setScorecard(data);
        if (data.live) {
          setLiveData((prev) => ({ ...prev, ...data.live }));
        }
        setError(null);
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err.response?.data?.detail || 'Failed to load match scorecard');
      }
    } finally {
      if (isMountedRef.current && isInitial) {
        setLoading(false);
      }
    }
  }, [matchId]);

  // Fallback Polling Handler (runs every 5s if socket is disconnected)
  const startFallbackPolling = useCallback(() => {
    if (pollingTimerRef.current) return;
    setIsPolling(true);
    pollingTimerRef.current = setInterval(async () => {
      if (!isMountedRef.current || !matchId) return;
      try {
        const live = await matchesService.getLiveState(matchId);
        if (isMountedRef.current && live) {
          setLiveData(live);
          setScorecard((prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              status: live.status || prev.status,
              live: { ...prev.live, ...live },
            };
          });
        }
      } catch (err) {
        // Silently tolerate intermittent poll hiccups
      }
    }, 5000);
  }, [matchId]);

  const stopFallbackPolling = useCallback(() => {
    if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }
    setIsPolling(false);
  }, []);

  // WebSocket Connection Handler
  const connectWebSocket = useCallback(() => {
    if (!matchId) return;

    // Clean up prior instance
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch (e) {}
      wsRef.current = null;
    }

    const wsBase = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';
    const wsUrl = `${wsBase}/ws/matches/${matchId}`;

    try {
      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        if (!isMountedRef.current) return;
        setIsConnected(true);
        stopFallbackPolling();

        // 15s Heartbeat ping
        if (heartbeatTimerRef.current) clearInterval(heartbeatTimerRef.current);
        heartbeatTimerRef.current = setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'ping' }));
          }
        }, 15000);
      };

      socket.onmessage = (event) => {
        if (!isMountedRef.current) return;
        try {
          const data = JSON.parse(event.data);
          if (data && data.type !== 'pong') {
            setLiveData(data);
            setScorecard((prev) => {
              if (!prev) return prev;
              return {
                ...prev,
                status: data.status || prev.status,
                live: { ...prev.live, ...data },
              };
            });
          }
        } catch (e) {
          // ignore non-json messages (e.g. text 'pong')
        }
      };

      socket.onerror = () => {
        if (!isMountedRef.current) return;
        setIsConnected(false);
        startFallbackPolling();
      };

      socket.onclose = () => {
        if (!isMountedRef.current) return;
        setIsConnected(false);
        startFallbackPolling();

        // Auto-reconnect after 3 seconds
        if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = setTimeout(() => {
          if (isMountedRef.current) {
            connectWebSocket();
          }
        }, 3000);
      };
    } catch (err) {
      setIsConnected(false);
      startFallbackPolling();
    }
  }, [matchId, startFallbackPolling, stopFallbackPolling]);

  useEffect(() => {
    isMountedRef.current = true;
    fetchScorecard(true);
    connectWebSocket();

    return () => {
      isMountedRef.current = false;
      stopFallbackPolling();
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (heartbeatTimerRef.current) clearInterval(heartbeatTimerRef.current);
      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch (e) {}
      }
    };
  }, [fetchScorecard, connectWebSocket, stopFallbackPolling]);

  return {
    scorecard,
    liveData,
    isConnected,
    isPolling,
    loading,
    error,
    refresh: () => fetchScorecard(false),
  };
}

export default useMatchSocket;

