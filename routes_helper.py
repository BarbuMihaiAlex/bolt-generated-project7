"""
Update create_container function to handle both port formats
"""

def create_container(container_manager, challenge_id: int, user_id: int, team_id: int, docker_assignment: str) -> Tuple[Dict[str, Any], int]:
    """
    Create a new container instance with support for both legacy and new port formats.
    """
    # ... [previous code remains the same until container creation] ...

    try:
        # Handle both legacy and new port formats
        port_data = challenge.port_mappings if challenge.ports else challenge.port
        
        created_container = container_manager.create_container(
            challenge.image,
            port_data,
            challenge.command,
            challenge.volumes
        )
    except Exception as e:
        log("containers_errors", 
            format="CHALL_ID:{challenge_id}|Container creation failed: {error}",
            challenge_id=challenge_id,
            error=str(e))
        return {"error": "Failed to create container"}, 500

    try:
        # Get port mappings
        port_mappings = container_manager.get_container_ports(created_container.id)
        if not port_mappings:
            log("containers_errors", 
                format="CHALL_ID:{challenge_id}|Could not get ports for container '{container_id}'",
                challenge_id=challenge_id,
                container_id=created_container.id)
            return {"error": "Could not get container ports"}, 500

        # Calculate expiration time
        expires = int(time.time() + container_manager.expiration_seconds)

        # Create new container record
        new_container = ContainerInfoModel(
            container_id=created_container.id,
            challenge_id=challenge.id,
            user_id=user_id,
            team_id=team_id,
            port=list(port_mappings.values())[0] if port_mappings else None,  # Legacy support
            ports=json.dumps(port_mappings),
            timestamp=int(time.time()),
            expires=expires
        )

        db.session.add(new_container)
        db.session.commit()

        return {
            "status": "created",
            "hostname": challenge.connection_info,
            "ports": port_mappings,
            "port_descriptions": challenge.port_mappings,
            "expires": expires
        }, 200

    except Exception as e:
        log("containers_errors", 
            format="CHALL_ID:{challenge_id}|Error saving container info: {error}",
            challenge_id=challenge_id,
            error=str(e))
        return {"error": "Failed to save container information"}, 500
