import boto3
import botocore
import click

session = boto3.Session(profile_name='shotty')
ec2 = session.resource('ec2')

def filter_instances(project):
    instances = []
    if project:
        filters = [{'Name':'tag:Project', 'Values':[project]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    return instances

@click.group()
def cli():
    """Shotty manages snapshots from AWS cloud"""

@cli.group('volumes')
def volumes():
    """Commands for volumes"""

@volumes.command('list')
@click.option('--project',default=None)
def list_volumes(project):
    "List all EC2 volumes"

    instances = filter_instances(project)
    for i in instances:
        for v in i.volumes.all():
            print (", ".join((
                v.id,
                i.id,
                v.state,
                str(v.size) + 'GiB',
                v.encrypted and "Encrpted" or "Not encrypted"
            )))

    return

@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option('--project',default=None)
def list_snapshots(project):
    "List all snapshots"
    instances = filter_instances(project)

    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print (", ".join((
                    s.id,
                    v.id,
                    i.id,
                    s.state,
                    s.progress,
                    s.start_time.strftime("%c")
                )))
    return

@cli.group('instances')
def instances():
    """Commands for instances"""

@instances.command('list')
@click.option('--project', default=None)
def list_instances(project):
    "List all EC2 instances"
    instances = filter_instances(project)
    for i in instances:
        tags = { t['Key']: t['Value'] for t in i.tags or []}
        print (', '.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state["Name"],
            i.public_dns_name,
            tags.get('Project', '<no project>')
            )))

    return

@instances.command('start')
@click.option('--project', default=None)
def start_instance(project):
    "Function to start instances"
    instances = filter_instances(project)

    for i in instances:
        print ("Starting: ", i.id)
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
            print (" Could not stop {0}. ".format(i.id)+str(e))
            continue
    return

@instances.command('stop')
@click.option('--project', default=None)
def start_instance(project):
    "Function to stop instances"
    instances = filter_instances(project)

    for i in instances:
        print ("Stopping: ", i.id)
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print (" Could not start {0}. ".format(i.id)+str(e))
            continue
    return

@instances.command('snapshot')
@click.option('--project',default=None)
def create_snapshot(project):
    "Creates snapshot of EC2 instances"

    instances = filter_instances(project)

    for i in instances:
        print ("Stopping {0}...".format(i.id))
        i.stop()
        i.wait_until_stopped()
        for v in i.volumes.all():
            print ("Creating snapshot of ", v.id)
            v.create_snapshot(Description="Created by AWS Instance Snapshots")
        print ("Starting {0}...".format(i.id))
        i.start()
        i.wait_until_running()

    print ("Job's done")
    return


if __name__ == '__main__':
    cli()
