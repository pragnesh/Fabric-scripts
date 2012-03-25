import getpass
from fabric.contrib.console import confirm
from fabric.operations import prompt, sudo, run
from fabric.state import env

env.hosts = ['192.168.2.159']
env.domain = "example.com"
env.directory = '/sites'

PACKAGES = {
    'build-essential',
    'git-core',
    'curl',
    'ntp',
    'python-dev',
    'libssl-dev',
    'libxml2-dev',  # nginx
    'libssl-dev',  # nginx
    'libpcre3-dev',  # nginx
    'nginx'
}


def create_user():
    """
    Creates a user with a home directory and adds him to the sudoers
    """
    prompt('Remote user username: ', 'new_username')
    env.new_password = getpass.getpass('Enter remote user password: ')

    run('useradd -m -s /bin/bash %s' % env.new_username)
    run('echo "%s ALL=(ALL) ALL" >> /etc/sudoers' % env.new_username)
    run('echo "%s:%s" | chpasswd' % (env.new_username, env.new_password))

    env.user = env.new_username
    env.password = env.new_password


def upgrade_and_update():
    """
    Basic upgrade and update
    """
    run('apt-get -y dist-upgrade')
    run('apt-get -y update')


def install_sudo():
    """
    No sudo by default on my server
    """
    run('apt-get -y install sudo')


def install_from_backports():
    """
    Install stuff from backports, here postgresql
    """
    sudo('apt-get -t squeeze-backports -y install postgresql-9.1')


def add_repos_to_list():
    """
    Add repos to the source.list file, in case you want more
    up to date programs
    Only nginx for now
    """
    run('echo "deb http://nginx.org/packages/debian/ squeeze nginx" >> /etc/apt/sources.list')
    run('echo "deb http://backports.debian.org/debian-backports squeeze-backports main" >> /etc/apt/sources.list')


def install_packages():
    """
    Install all the packages listed on the top of the file
    """
    for p in PACKAGES:
        sudo('apt-get -y install %s --force-yes' % p)


def create_postgresql_user():
    """
    Create an admin user for postgresql
    You can modify permissions later using pgadmin
    """
    prompt('Database user username: ', 'db_username')
    env.db_password = getpass.getpass('Enter postgresql user password: ')
    sudo('psql -c "CREATE USER %s WITH PASSWORD \'%s\' SUPERUSER;"'
        % (env.db_username, env.db_password), user='postgres')


def install_and_configure_postfix():
    """
    Install a basic postfix instance
    """
    sudo('DEBIAN_FRONTEND=noninteractive apt-get -y install postfix')
    sudo('postconf -e "myorigin = %s"' % env.domain)
    hostname = sudo('hostname')
    sudo('postconf -e "myhostname = %s"' % hostname)
    sudo('postfix reload')


def create_websites_directory():
    """
    I prefer using a basic one at the root called /sites
    """
    sudo('mkdir -p %s' % env.directory)
    sudo('chown %s:%s %s' % (env.user, env.user, env.directory))


def server_setup():
    """
    Main method that calls all the others
    """
    # First we need the root password
    env.user = 'root'
    env.password = getpass.getpass('Enter remote root password: ')

    add_repos_to_list()
    upgrade_and_update()
    install_sudo()
    create_user()
    install_packages()
    install_from_backports()
    create_postgresql_user()
    create_websites_directory()
    if confirm("Do you want to install postfix? "):
        install_and_configure_postfix()
