package com.example.orderservice.service;
import com.example.orderservice.domain.Order;
import com.example.orderservice.repository.OrderRepository;
import com.example.orderservice.dto.Event;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class OrderConsumerService {
    @Autowired
    private OrderRepository orderRepository;

    @RabbitListener(queues = "order.status.payment.queue")
    public void onPaymentProcessed(Event event) {
        updateOrderStatus(event.getAggregateId(), "PAID");
    }
    
    @RabbitListener(queues = "order.status.inventory.queue")
    public void onInventoryReserved(Event event) {
        updateOrderStatus(event.getAggregateId(), "INVENTORY_RESERVED");
    }
    
    @RabbitListener(queues = "order.status.shipment.queue")
    public void onShipmentCreated(Event event) {
        updateOrderStatus(event.getAggregateId(), "SHIPPED");
    }
    
    private void updateOrderStatus(String orderId, String status) {
        orderRepository.findById(orderId).ifPresent(order -> {
            order.setStatus(status);
            orderRepository.save(order);
        });
    }
}