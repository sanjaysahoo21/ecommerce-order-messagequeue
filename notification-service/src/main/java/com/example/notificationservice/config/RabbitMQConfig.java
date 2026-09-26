package com.example.notificationservice.config;
import org.springframework.amqp.core.*;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {
    @Bean
    public TopicExchange exchange() { return new TopicExchange("order_exchange", true, false); }
    
    @Bean
    public Queue notificationQueue() { return new Queue("notification.queue", true); }
    
    // Bind to all events
    @Bean
    public Binding bindOrder() { return BindingBuilder.bind(notificationQueue()).to(exchange()).with("order.created"); }
    @Bean
    public Binding bindPayment() { return BindingBuilder.bind(notificationQueue()).to(exchange()).with("payment.processed"); }
    @Bean
    public Binding bindInventory() { return BindingBuilder.bind(notificationQueue()).to(exchange()).with("inventory.reserved"); }
    @Bean
    public Binding bindShipment() { return BindingBuilder.bind(notificationQueue()).to(exchange()).with("shipment.created"); }
    
    @Bean
    public MessageConverter converter() { return new Jackson2JsonMessageConverter(); }
}