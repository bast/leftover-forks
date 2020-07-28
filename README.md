

# leftover-forks

This project goes through all the forks under my namespace and lists those
which are either untouched or merged upstream and can thus probably be deleted.

- [generated list](../generated/leftover-forks.md)


### Inspiration and how it works

The script does it using the following steps:
- It gets a list of all the forks under the namespace `GITHUB_USER`
- For each of these forks it gets the hashes of all branches on this fork
- Then it checks whether these hashes are part of the parent repo
  - Note that checking whether the parent repo contains the hash is not enough ([this surprised me](https://twitter.com/__radovan/status/1254012382407536640))
  - It finds out which branches exist on the parent repo
  - For each hash it first tries to compare with the corresponding branch on the parent repo
  - If such a branch does not exist, it compares with the default branch

If you like it, you can use it yourself, all you need to do is to adapt
`GITHUB_USER` and obtain a personal access token and add it to your secrets:
https://github.com/bast/leftover-forks/blob/master/.github/workflows/build.yml#L25-L26

The only permission the personal access token needs is `public_repo` (be able
to read public repositories).

I learned from
https://simonwillison.net/2020/Jul/10/self-updating-profile-readme/ and
https://github.com/simonw/simonw that one can run cron jobs as part of a GitHub
Action and my workflow file is based on the workflow found in
https://github.com/simonw/simonw.
