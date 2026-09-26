package com.example.paymentservice.config;
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
    public Queue paymentQueue() { return new Queue("payment.queue", true); }
    @Bean
    public Binding binding() { return BindingBuilder.bind(paymentQueue()).to(exchange()).with("order.created"); }
    @Bean
    public MessageConverter converter() { return new Jackson2JsonMessageConverter(); }
}