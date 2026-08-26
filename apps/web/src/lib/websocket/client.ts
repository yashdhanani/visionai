import { useEffect, useRef, useState, useCallback } from "react";

type WebSocketMessage = {
  type: string;
  [key: string]: unknown;
};

type Detection = {
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: { x: number; y: number; width: number; height: number };
  track_id?: number | null;
};

type DetectionResult = {
  type: "detection";
  category: string;
  seq: number;
  ts: number;
  detections: Detection[];
  performance: {
    fps: number;
    latency_ms: number;
    preprocess_ms: number;
    inference_ms: number;
    postprocess_ms: number;
  };
  frame_width: number;
  frame_height: number;
  count: number;
  category_data?: unknown;
};

type WebSocketHookOptions = {
  onMessage?: (msg: WebSocketMessage) => void;
  onDetection?: (result: DetectionResult) => void;
  onError?: (error: string) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
};

export function useWebSocket(
  url: string | null,
  options: WebSocketHookOptions = {}
) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const sendMessage = useCallback(
    (data: unknown) => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(typeof data === "string" ? data : JSON.stringify(data));
        return true;
      }
      return false;
    },
    []
  );

  const close = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!url) return;
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        reconnectAttempts.current = 0;
        options.onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data) as WebSocketMessage;
          setLastMessage(msg);
          options.onMessage?.(msg);
          if (msg.type === "detection") {
            options.onDetection?.(msg as DetectionResult);
          }
        } catch (err) {
          // ignore parse errors
        }
      };

      ws.onerror = (event) => {
        options.onError?.("WebSocket error");
      };

      ws.onclose = () => {
        setIsConnected(false);
        options.onDisconnect?.();
        // Attempt reconnect
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 1000 * reconnectAttempts.current);
        }
      };
    } catch (err) {
      options.onError?.(String(err));
    }
  }, [url, options]);

  useEffect(() => {
    connect();
    return () => {
      close();
    };
  }, [connect, close]);

  return { isConnected, sendMessage, close, lastMessage };
}