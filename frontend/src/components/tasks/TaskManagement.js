import React, { useState } from 'react';
import { Container, Row, Col, Nav, Tab } from 'react-bootstrap';
import TaskCreateForm from './TaskCreateForm';
import TaskList from './TaskList';

const TaskManagement = () => {
    const [refreshList, setRefreshList] = useState(0);
    
    // Mock current user - in production this would come from auth context
    const currentUser = {
        id: 'user123',
        name: 'Current User'
    };

    const handleTaskCreated = (newTask) => {
        // Trigger list refresh when a new task is created
        setRefreshList(prev => prev + 1);
    };

    return (
        <Container fluid className="py-4">
            <h2 className="mb-4">Uppgiftshantering</h2>
            
            <Tab.Container defaultActiveKey="list">
                <Nav variant="tabs" className="mb-3">
                    <Nav.Item>
                        <Nav.Link eventKey="list">Uppgiftslista</Nav.Link>
                    </Nav.Item>
                    <Nav.Item>
                        <Nav.Link eventKey="create">Skapa ny uppgift</Nav.Link>
                    </Nav.Item>
                </Nav>
                
                <Tab.Content>
                    <Tab.Pane eventKey="list">
                        <TaskList 
                            key={refreshList} 
                            currentUser={currentUser}
                        />
                    </Tab.Pane>
                    <Tab.Pane eventKey="create">
                        <Row>
                            <Col lg={8} className="mx-auto">
                                <TaskCreateForm 
                                    onTaskCreated={handleTaskCreated}
                                    currentUser={currentUser}
                                />
                            </Col>
                        </Row>
                    </Tab.Pane>
                </Tab.Content>
            </Tab.Container>
        </Container>
    );
};

export default TaskManagement;
