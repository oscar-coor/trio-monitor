import React, { useState, useEffect } from 'react';
import { Table, Badge, Button, Card, Form, Row, Col, Modal, Alert, InputGroup } from 'react-bootstrap';
import axios from 'axios';
import { FaEdit, FaTrash, FaComment, FaSync, FaSearch, FaFilter } from 'react-icons/fa';

const TaskList = ({ currentUser }) => {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({
        status: '',
        priority: '',
        assigned_to: '',
        service_id: '',
        search: ''
    });
    const [selectedTask, setSelectedTask] = useState(null);
    const [showEditModal, setShowEditModal] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [showCommentModal, setShowCommentModal] = useState(false);
    const [editFormData, setEditFormData] = useState({});
    const [commentText, setCommentText] = useState('');
    const [users, setUsers] = useState([]);
    const [services, setServices] = useState([]);

    useEffect(() => {
        fetchTasks();
        fetchUsers();
        fetchServices();
    }, [filters]);

    const fetchTasks = async () => {
        setLoading(true);
        try {
            const params = {};
            Object.keys(filters).forEach(key => {
                if (filters[key]) params[key] = filters[key];
            });

            const response = await axios.get('http://localhost:8000/api/tasks/', { params });
            setTasks(response.data.tasks || response.data);
        } catch (err) {
            setError('Failed to fetch tasks');
            console.error(err);
        } finally {
            setLoading(false);
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

    const fetchServices = async () => {
        try {
            const response = await axios.get('http://localhost:8000/api/admin/services');
            setServices(response.data);
        } catch (err) {
            console.error('Failed to fetch services:', err);
        }
    };

    const handleFilterChange = (e) => {
        const { name, value } = e.target;
        setFilters(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleEdit = (task) => {
        setSelectedTask(task);
        setEditFormData({
            title: task.title,
            description: task.description,
            status: task.status,
            priority: task.priority,
            assigned_to: task.assigned_to || '',
            assigned_to_name: task.assigned_to_name || '',
            due_date: task.due_date ? new Date(task.due_date).toISOString().slice(0, 16) : ''
        });
        setShowEditModal(true);
    };

    const handleEditSubmit = async () => {
        try {
            const payload = {
                ...editFormData,
                updated_by: currentUser?.id || 'system',
                updated_by_name: currentUser?.name || 'System',
                due_date: editFormData.due_date ? new Date(editFormData.due_date).toISOString() : null
            };

            await axios.put(`http://localhost:8000/api/tasks/${selectedTask.id}`, payload);
            setShowEditModal(false);
            fetchTasks();
        } catch (err) {
            console.error('Failed to update task:', err);
            alert('Failed to update task');
        }
    };

    const handleDelete = (task) => {
        setSelectedTask(task);
        setShowDeleteModal(true);
    };

    const confirmDelete = async () => {
        try {
            await axios.delete(`http://localhost:8000/api/tasks/${selectedTask.id}`);
            setShowDeleteModal(false);
            fetchTasks();
        } catch (err) {
            console.error('Failed to delete task:', err);
            alert('Failed to delete task');
        }
    };

    const handleComment = (task) => {
        setSelectedTask(task);
        setCommentText('');
        setShowCommentModal(true);
    };

    const submitComment = async () => {
        try {
            await axios.post(`http://localhost:8000/api/tasks/${selectedTask.id}/comments`, {
                content: commentText,
                author_id: currentUser?.id || 'system',
                author_name: currentUser?.name || 'System'
            });
            setShowCommentModal(false);
            setCommentText('');
        } catch (err) {
            console.error('Failed to add comment:', err);
            alert('Failed to add comment');
        }
    };

    const getPriorityBadge = (priority) => {
        const variants = {
            low: 'secondary',
            medium: 'info',
            high: 'warning',
            urgent: 'danger'
        };
        const labels = {
            low: 'Låg',
            medium: 'Medium',
            high: 'Hög',
            urgent: 'Brådskande'
        };
        return <Badge bg={variants[priority]}>{labels[priority]}</Badge>;
    };

    const getStatusBadge = (status) => {
        const variants = {
            pending: 'secondary',
            in_progress: 'primary',
            completed: 'success',
            cancelled: 'dark'
        };
        const labels = {
            pending: 'Väntande',
            in_progress: 'Pågående',
            completed: 'Slutförd',
            cancelled: 'Avbruten'
        };
        return <Badge bg={variants[status]}>{labels[status]}</Badge>;
    };

    const formatDate = (dateString) => {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleString('sv-SE', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <Card>
            <Card.Header>
                <div className="d-flex justify-content-between align-items-center">
                    <h4>Uppgifter</h4>
                    <Button variant="outline-primary" size="sm" onClick={fetchTasks}>
                        <FaSync /> Uppdatera
                    </Button>
                </div>
            </Card.Header>
            <Card.Body>
                {/* Filters */}
                <Row className="mb-3">
                    <Col md={3}>
                        <InputGroup>
                            <InputGroup.Text><FaSearch /></InputGroup.Text>
                            <Form.Control
                                type="text"
                                placeholder="Sök uppgifter..."
                                name="search"
                                value={filters.search}
                                onChange={handleFilterChange}
                            />
                        </InputGroup>
                    </Col>
                    <Col md={2}>
                        <Form.Select name="status" value={filters.status} onChange={handleFilterChange}>
                            <option value="">Alla status</option>
                            <option value="pending">Väntande</option>
                            <option value="in_progress">Pågående</option>
                            <option value="completed">Slutförd</option>
                            <option value="cancelled">Avbruten</option>
                        </Form.Select>
                    </Col>
                    <Col md={2}>
                        <Form.Select name="priority" value={filters.priority} onChange={handleFilterChange}>
                            <option value="">Alla prioriteter</option>
                            <option value="low">Låg</option>
                            <option value="medium">Medium</option>
                            <option value="high">Hög</option>
                            <option value="urgent">Brådskande</option>
                        </Form.Select>
                    </Col>
                    <Col md={2}>
                        <Form.Select name="assigned_to" value={filters.assigned_to} onChange={handleFilterChange}>
                            <option value="">Alla användare</option>
                            {users.map(user => (
                                <option key={user.id} value={user.id}>{user.name}</option>
                            ))}
                        </Form.Select>
                    </Col>
                    <Col md={2}>
                        <Form.Select name="service_id" value={filters.service_id} onChange={handleFilterChange}>
                            <option value="">Alla tjänster</option>
                            {services.map(service => (
                                <option key={service.service_id} value={service.service_id}>
                                    {service.name}
                                </option>
                            ))}
                        </Form.Select>
                    </Col>
                    <Col md={1}>
                        <Button 
                            variant="outline-secondary" 
                            onClick={() => setFilters({
                                status: '',
                                priority: '',
                                assigned_to: '',
                                service_id: '',
                                search: ''
                            })}
                        >
                            <FaFilter /> Rensa
                        </Button>
                    </Col>
                </Row>

                {/* Tasks Table */}
                {loading ? (
                    <div className="text-center">Laddar uppgifter...</div>
                ) : error ? (
                    <Alert variant="danger">{error}</Alert>
                ) : (
                    <Table striped hover responsive>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Titel</th>
                                <th>Status</th>
                                <th>Prioritet</th>
                                <th>Tilldelad till</th>
                                <th>Tjänst</th>
                                <th>Skapad</th>
                                <th>Förfaller</th>
                                <th>Åtgärder</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tasks.length === 0 ? (
                                <tr>
                                    <td colSpan="9" className="text-center">Inga uppgifter hittades</td>
                                </tr>
                            ) : (
                                tasks.map(task => (
                                    <tr key={task.id}>
                                        <td>{task.id}</td>
                                        <td>
                                            <strong>{task.title}</strong>
                                            {task.description && (
                                                <div className="text-muted small">
                                                    {task.description.substring(0, 50)}
                                                    {task.description.length > 50 && '...'}
                                                </div>
                                            )}
                                        </td>
                                        <td>{getStatusBadge(task.status)}</td>
                                        <td>{getPriorityBadge(task.priority)}</td>
                                        <td>{task.assigned_to_name || '-'}</td>
                                        <td>{task.service_name || '-'}</td>
                                        <td>{formatDate(task.created_at)}</td>
                                        <td>{formatDate(task.due_date)}</td>
                                        <td>
                                            <div className="d-flex gap-1">
                                                <Button 
                                                    variant="outline-primary" 
                                                    size="sm"
                                                    onClick={() => handleEdit(task)}
                                                    title="Redigera"
                                                >
                                                    <FaEdit />
                                                </Button>
                                                <Button 
                                                    variant="outline-info" 
                                                    size="sm"
                                                    onClick={() => handleComment(task)}
                                                    title="Kommentera"
                                                >
                                                    <FaComment />
                                                </Button>
                                                <Button 
                                                    variant="outline-danger" 
                                                    size="sm"
                                                    onClick={() => handleDelete(task)}
                                                    title="Ta bort"
                                                >
                                                    <FaTrash />
                                                </Button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </Table>
                )}
            </Card.Body>

            {/* Edit Modal */}
            <Modal show={showEditModal} onHide={() => setShowEditModal(false)} size="lg">
                <Modal.Header closeButton>
                    <Modal.Title>Redigera uppgift</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form>
                        <Form.Group className="mb-3">
                            <Form.Label>Titel</Form.Label>
                            <Form.Control
                                type="text"
                                value={editFormData.title || ''}
                                onChange={(e) => setEditFormData({...editFormData, title: e.target.value})}
                            />
                        </Form.Group>
                        <Form.Group className="mb-3">
                            <Form.Label>Beskrivning</Form.Label>
                            <Form.Control
                                as="textarea"
                                rows={3}
                                value={editFormData.description || ''}
                                onChange={(e) => setEditFormData({...editFormData, description: e.target.value})}
                            />
                        </Form.Group>
                        <Row>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Status</Form.Label>
                                    <Form.Select 
                                        value={editFormData.status || ''}
                                        onChange={(e) => setEditFormData({...editFormData, status: e.target.value})}
                                    >
                                        <option value="pending">Väntande</option>
                                        <option value="in_progress">Pågående</option>
                                        <option value="completed">Slutförd</option>
                                        <option value="cancelled">Avbruten</option>
                                    </Form.Select>
                                </Form.Group>
                            </Col>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Prioritet</Form.Label>
                                    <Form.Select 
                                        value={editFormData.priority || ''}
                                        onChange={(e) => setEditFormData({...editFormData, priority: e.target.value})}
                                    >
                                        <option value="low">Låg</option>
                                        <option value="medium">Medium</option>
                                        <option value="high">Hög</option>
                                        <option value="urgent">Brådskande</option>
                                    </Form.Select>
                                </Form.Group>
                            </Col>
                        </Row>
                        <Form.Group className="mb-3">
                            <Form.Label>Förfallodatum</Form.Label>
                            <Form.Control
                                type="datetime-local"
                                value={editFormData.due_date || ''}
                                onChange={(e) => setEditFormData({...editFormData, due_date: e.target.value})}
                            />
                        </Form.Group>
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowEditModal(false)}>
                        Avbryt
                    </Button>
                    <Button variant="primary" onClick={handleEditSubmit}>
                        Spara ändringar
                    </Button>
                </Modal.Footer>
            </Modal>

            {/* Delete Confirmation Modal */}
            <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
                <Modal.Header closeButton>
                    <Modal.Title>Bekräfta borttagning</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    Är du säker på att du vill ta bort uppgiften "{selectedTask?.title}"?
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
                        Avbryt
                    </Button>
                    <Button variant="danger" onClick={confirmDelete}>
                        Ta bort
                    </Button>
                </Modal.Footer>
            </Modal>

            {/* Comment Modal */}
            <Modal show={showCommentModal} onHide={() => setShowCommentModal(false)}>
                <Modal.Header closeButton>
                    <Modal.Title>Lägg till kommentar</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form.Group>
                        <Form.Label>Kommentar</Form.Label>
                        <Form.Control
                            as="textarea"
                            rows={4}
                            value={commentText}
                            onChange={(e) => setCommentText(e.target.value)}
                            placeholder="Skriv din kommentar här..."
                        />
                    </Form.Group>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowCommentModal(false)}>
                        Avbryt
                    </Button>
                    <Button variant="primary" onClick={submitComment} disabled={!commentText.trim()}>
                        Skicka kommentar
                    </Button>
                </Modal.Footer>
            </Modal>
        </Card>
    );
};

export default TaskList;
