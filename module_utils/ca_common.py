import os
import datetime


def generate_cmd(sub_cmd, args, binary='ceph', user_key=None, cluster='ceph', user='client.admin', container_image=None, interactive=False):
    '''
    Generate 'ceph' command line to execute
    '''

    if not user_key:
        user_key = '/etc/ceph/{}.{}.keyring'.format(cluster, user)

    if container_image:
        cmd = container_exec(binary, container_image, interactive=interactive)
    else:
        cmd = [binary]

    base_cmd = [
        '-n',
        user,
        '-k',
        user_key,
        '--cluster',
        cluster
    ]
    base_cmd.extend(sub_cmd)
    cmd.extend(base_cmd + args)

    return cmd


def container_exec(binary, container_image, interactive=False):
    '''
    Build the docker CLI to run a command inside a container
    '''

    container_binary = os.getenv('CEPH_CONTAINER_BINARY')
    command_exec = [container_binary, 'run']

    if interactive:
        command_exec.extend(['--interactive'])

    command_exec.extend(['--rm',
                         '--net=host',
                         '-v', '/etc/ceph:/etc/ceph:z',
                         '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                         '-v', '/var/log/ceph/:/var/log/ceph/:z',
                         '--entrypoint=' + binary, container_image])
    return command_exec


def is_containerized():
    '''
    Check if we are running on a containerized cluster
    '''

    if 'CEPH_CONTAINER_IMAGE' in os.environ:
        container_image = os.getenv('CEPH_CONTAINER_IMAGE')
    else:
        container_image = None

    return container_image


def exec_command(module, cmd, stdin=None):
    '''
    Execute command(s)
    '''

    binary_data = False
    if stdin:
        binary_data = True
    rc, out, err = module.run_command(cmd, data=stdin, binary_data=binary_data)

    return rc, cmd, out, err


def exit_module(module, out, rc, cmd, err, startd, changed=False):
    endd = datetime.datetime.now()
    delta = endd - startd

    result = dict(
        cmd=cmd,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        rc=rc,
        stdout=out.rstrip("\r\n"),
        stderr=err.rstrip("\r\n"),
        changed=changed,
    )
    module.exit_json(**result)


def fatal(message, module):
    '''
    Report a fatal error and exit
    '''

    if module:
        module.fail_json(msg=message, rc=1)
    else:
        raise(Exception(message))
