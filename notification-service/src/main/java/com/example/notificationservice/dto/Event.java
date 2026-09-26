package com.example.notificationservice.dto;

import java.util.Map;

public class Event {
    private String eventId;
    private String eventType;
    private String timestamp;
    private String aggregateId;
    private Map<String, Object> payload;

    public Event() {}

    public Event(String eventId, String eventType, String timestamp, String aggregateId, Map<String, Object> payload) {
        this.eventId = eventId;
        this.eventType = eventType;
        this.timestamp = timestamp;
        this.aggregateId = aggregateId;
        this.payload = payload;
    }

    public String getEventId() { return eventId; }
    public void setEventId(String eventId) { this.eventId = eventId; }
    public String getEventType() { return eventType; }
    public void setEventType(String eventType) { this.eventType = eventType; }
    public String getTimestamp() { return timestamp; }
    public void setTimestamp(String timestamp) { this.timestamp = timestamp; }
    public String getAggregateId() { return aggregateId; }
    public void setAggregateId(String aggregateId) { this.aggregateId = aggregateId; }
    public Map<String, Object> getPayload() { return payload; }
    public void setPayload(Map<String, Object> payload) { this.payload = payload; }
}