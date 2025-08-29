import React, { useState, useEffect } from 'react';
import { Form, Button, Card, Alert, Row, Col } from 'react-bootstrap';
import axios from 'axios';

const TaskCreateForm = ({ onTaskCreated, currentUser }) => {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        priority: 'medium',
        status: 'pending',
        assigned_to: '',
        assigned_to_name: '',
        service_id: '',
        service_name: '',
        category_id: null,
        due_date: ''
    });

    const [categories, setCategories] = useState([]);
    const [services, setServices] = useState([]);
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        fetchCategories();
        fetchServices();
        fetchUsers();
    }, []);

    const fetchCategories = async () => {
        try {
            const response = await axios.get('http://localhost:8000/api/tasks/categories/');
            setCategories(response.data);
        } catch (err) {
            console.error('Failed to fetch categories:', err);
        }
    };

    const fetchServices = async () => {
        try {
            const response = await axios.get('http://localhost:8000/api/admin/services');
            setServices(response.data);
        } catch (err) {
            console.error('Failed to fetch services:', err);
        }
    };

    const fetchUsers = async () => {
        try {
            const response = await axios.get('http://localhost:8000/api/admin/users');
            setUsers(response.data);
        } catch (err) {
            console.error('Failed to fetch users:', err);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));

        // Auto-fill names when IDs are selected
        if (name === 'assigned_to') {
            const user = users.find(u => u.id === value);
            if (user) {
                setFormData(prev => ({
                    ...prev,
                    assigned_to_name: user.name
                }));
            }
        }
        if (name === 'service_id') {
            const service = services.find(s => s.service_id === value);
            if (service) {
                setFormData(prev => ({
                    ...prev,
                    service_name: service.name
                }));
            }
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(false);

        try {
            const payload = {
                ...formData,
                created_by: currentUser?.id || 'system',
                created_by_name: currentUser?.name || 'System',
                category_id: formData.category_id ? parseInt(formData.category_id) : null,
                due_date: formData.due_date ? new Date(formData.due_date).toISOString() : null
            };

            const response = await axios.post('http://localhost:8000/api/tasks/', payload);
            
            setSuccess(true);
            setFormData({
                title: '',
                description: '',
                priority: 'medium',
                status: 'pending',
                assigned_to: '',
                assigned_to_name: '',
                service_id: '',
                service_name: '',
                category_id: null,
                due_date: ''
            });

            if (onTaskCreated) {
                onTaskCreated(response.data);
            }

            setTimeout(() => setSuccess(false), 3000);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to create task');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card className="mb-4">
            <Card.Header>
                <h4>Skapa ny uppgift</h4>
            </Card.Header>
            <Card.Body>
                {error && <Alert variant="danger" dismissible onClose={() => setError(null)}>{error}</Alert>}
                {success && <Alert variant="success">Uppgift skapad!</Alert>}
                
                <Form onSubmit={handleSubmit}>
                    <Row>
                        <Col md={6}>
                            <Form.Group className="mb-3">
                                <Form.Label>Titel *</Form.Label>
                                <Form.Control
                                    type="text"
                                    name="title"
                                    value={formData.title}
                                    onChange={handleChange}
                                    required
                                    placeholder="Ange uppgiftens titel"
                                />
                            </Form.Group>
                        </Col>
                        <Col md={3}>
                            <Form.Group className="mb-3">
                                <Form.Label>Prioritet</Form.Label>
                                <Form.Select name="priority" value={formData.priority} onChange={handleChange}>
                                    <option value="low">Låg</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">Hög</option>
                                    <option value="urgent">Brådskande</option>
                                </Form.Select>
                            </Form.Group>
                        </Col>
                        <Col md={3}>
                            <Form.Group className="mb-3">
                                <Form.Label>Status</Form.Label>
                                <Form.Select name="status" value={formData.status} onChange={handleChange}>
                                    <option value="pending">Väntande</option>
                                    <option value="in_progress">Pågående</option>
                                    <option value="completed">Slutförd</option>
                                    <option value="cancelled">Avbruten</option>
                                </Form.Select>
                            </Form.Group>
                        </Col>
                    </Row>

                    <Form.Group className="mb-3">
                        <Form.Label>Beskrivning</Form.Label>
                        <Form.Control
                            as="textarea"
                            rows={3}
                            name="description"
                            value={formData.description}
                            onChange={handleChange}
                            placeholder="Beskriv uppgiften..."
                        />
                    </Form.Group>

                    <Row>
                        <Col md={4}>
                            <Form.Group className="mb-3">
                                <Form.Label>Tilldelad till</Form.Label>
                                <Form.Select 
                                    name="assigned_to" 
                                    value={formData.assigned_to} 
                                    onChange={handleChange}
                                >
                                    <option value="">Ej tilldelad</option>
                                    {users.map(user => (
                                        <option key={user.id} value={user.id}>
                                            {user.name}
                                        </option>
                                    ))}
                                </Form.Select>
                            </Form.Group>
                        </Col>
                        <Col md={4}>
                            <Form.Group className="mb-3">
                                <Form.Label>Tjänst/Kö</Form.Label>
                                <Form.Select 
                                    name="service_id" 
                                    value={formData.service_id} 
                                    onChange={handleChange}
                                >
                                    <option value="">Ingen</option>
                                    {services.map(service => (
                                        <option key={service.service_id} value={service.service_id}>
                                            {service.name}
                                        </option>
                                    ))}
                                </Form.Select>
                            </Form.Group>
                        </Col>
                        <Col md={4}>
                            <Form.Group className="mb-3">
                                <Form.Label>Kategori</Form.Label>
                                <Form.Select 
                                    name="category_id" 
                                    value={formData.category_id || ''} 
                                    onChange={handleChange}
                                >
                                    <option value="">Ingen kategori</option>
                                    {categories.map(cat => (
                                        <option key={cat.id} value={cat.id}>
                                            {cat.name}
                                        </option>
                                    ))}
                                </Form.Select>
                            </Form.Group>
                        </Col>
                    </Row>

                    <Form.Group className="mb-3">
                        <Form.Label>Förfallodatum</Form.Label>
                        <Form.Control
                            type="datetime-local"
                            name="due_date"
                            value={formData.due_date}
                            onChange={handleChange}
                        />
                    </Form.Group>

                    <div className="d-flex justify-content-end gap-2">
                        <Button variant="secondary" type="reset" onClick={() => setFormData({
                            title: '',
                            description: '',
                            priority: 'medium',
                            status: 'pending',
                            assigned_to: '',
                            assigned_to_name: '',
                            service_id: '',
                            service_name: '',
                            category_id: null,
                            due_date: ''
                        })}>
                            Rensa
                        </Button>
                        <Button variant="primary" type="submit" disabled={loading || !formData.title}>
                            {loading ? 'Skapar...' : 'Skapa uppgift'}
                        </Button>
                    </div>
                </Form>
            </Card.Body>
        </Card>
    );
};

export default TaskCreateForm;
