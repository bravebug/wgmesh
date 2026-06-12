# bash completion for wgmesh

_wgmesh_completion()
{
    local cur prev words cword
    _init_completion -n : || return

    local global_opts="--mesh-dir --output-dir -h --help"
    local commands="init build fill"

    case "${cword}" in
        1)
            COMPREPLY=( $(compgen -W "${global_opts} ${commands}" -- "$cur") )
            return
            ;;
    esac

    local cmd=""
    local word
    for word in "${words[@]}"; do
        case "$word" in
            build|fill)
                cmd="$word"
                break
                ;;
        esac
    done

    case "$prev" in
        --mesh-dir|--output-dir)
            _filedir -d
            return
            ;;
    esac

    case "$cmd" in
        init)
            COMPREPLY=( $(compgen -W "--force -h --help" -- "$cur") )
            return
            ;;
        build)
            COMPREPLY=( $(compgen -W "--clean --dry-run -h --help" -- "$cur") )
            return
            ;;
        fill)
            COMPREPLY=( $(compgen -W "--build -h --help" -- "$cur") )
            return
            ;;
        *)
            COMPREPLY=( $(compgen -W "${global_opts} ${commands}" -- "$cur") )
            return
            ;;
    esac
}

complete -F _wgmesh_completion wgmesh
