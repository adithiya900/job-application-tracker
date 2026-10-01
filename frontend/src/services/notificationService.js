const API_BASE_URL = "http://127.0.0.1:5000";

const localStatusChanges = new Map();

export function trackLocalStatusChange(applicationId, newStatus) {
  const key = `${applicationId}-${newStatus}`;
  localStatusChanges.set(key, Date.now());
  setTimeout(() => localStatusChanges.delete(key), 5000);
}

export function isLocalStatusChange(applicationId, newStatus) {
  const key = `${applicationId}-${newStatus}`;
  const timestamp = localStatusChanges.get(key);
  if (!timestamp) {
    return false;
  }
  return Date.now() - timestamp < 5000;
}

export function connectToNotificationStream(onNotification, onError) {
  const token = localStorage.getItem("access_token");

  if (!token) {
    return null;
  }

  const abortController = new AbortController();

  (async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/notifications/stream`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "text/event-stream",
          },
          signal: abortController.signal,
        }
      );

      if (!response.ok) {
        throw new Error(
          `Notification stream failed: ${response.status}`
        );
      }

      if (!response.body) {
        throw new Error("SSE response body is not available");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let buffer = "";

      while (true) {
        if (abortController.signal.aborted) {
          break;
        }

        const { value, done } = await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(value, {
          stream: true,
        });

        const events = buffer.split("\n\n");

        buffer = events.pop() || "";

        for (const event of events) {
          if (event.startsWith(":")) {
            continue;
          }

          const lines = event.split("\n");

          const eventLine = lines.find((line) =>
            line.startsWith("event:")
          );
          const dataLine = lines.find((line) =>
            line.startsWith("data:")
          );

          if (!eventLine) {
            continue;
          }

          const eventType = eventLine
            .replace(/^event:\s*/, "")
            .trim();

          if (eventType !== "notification") {
            continue;
          }

          if (!dataLine) {
            continue;
          }

          const jsonData = dataLine
            .replace(/^data:\s*/, "")
            .trim();

          if (!jsonData) {
            continue;
          }

          try {
            const notification = JSON.parse(jsonData);

            if (notification.message) {
              onNotification(notification);
            }
          } catch (parseError) {
            console.error(
              "Failed to parse notification:",
              parseError
            );
          }
        }
      }

      reader.releaseLock();
    } catch (error) {
      if (abortController.signal.aborted) {
        return;
      }

      console.error(
        "Notification stream error:",
        error
      );

      if (onError) {
        onError(error);
      }
    }
  })();

  return {
    abort: () => abortController.abort(),
  };
}
